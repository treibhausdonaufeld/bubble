"""Temporal.io workflows for item processing.

Workflows in Temporal orchestrate activities and handle the business logic.
They must be deterministic and use only Temporal APIs for side effects.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

# Pass the activities through the sandbox
with workflow.unsafe.imports_passed_through():
    from bubble.items.temporal.temporal_activities import (
        ItemImageResult,
        ItemProcessingRequest,
        SimilaritySearchRequest,
        analyze_image,
        fetch_item_images,
        generate_item_embedding,
        generate_search_embedding,
        save_item_suggestions,
        save_search_results,
        summarize_image_suggestions,
    )

logger = logging.getLogger(__name__)


@workflow.defn
class ItemProcessingWorkflow:
    """Workflow for processing item images and generating suggestions.

    This workflow orchestrates the complete image processing pipeline:
    1. Analyze uploaded images using AI/ML
    2. Generate title and description suggestions
    3. Update the item with suggestions
    4. Send notification to user
    5. Handle retries and errors gracefully
    """

    @workflow.run
    async def run(self, item_input_data: ItemProcessingRequest) -> dict[str, Any]:
        """Run the image processing workflow.

        Args:
            item_id: The ID of the item to process.
            user_id: The ID of the user who owns the item.

        Returns:
            dict: Processing result with status and suggestions.
        """
        workflow.logger.info(
            "Starting image processing workflow for item %s",
            item_input_data.item_id,
        )

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        try:
            # Step 1: Fetch images
            workflow.logger.info("Fetching images for item %s", item_input_data.item_id)
            images_data: list[ItemImageResult] = await workflow.execute_activity(
                fetch_item_images,
                args=[item_input_data],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            # create an own processing activity for each image
            workflow.logger.info(
                "Fetched %d images for item %s",
                len(images_data),
                item_input_data.item_id,
            )

            # Process all images in parallel
            image_tasks = [
                workflow.execute_activity(
                    analyze_image,
                    args=[image_data],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                for image_data in images_data
            ]

            image_suggestions = await asyncio.gather(*image_tasks)

            item_result = await workflow.execute_activity(
                summarize_image_suggestions,
                args=[image_suggestions],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )

            await workflow.execute_activity(
                save_item_suggestions,
                args=[item_result],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )

            workflow.logger.info(
                "Successfully completed processing for item %s",
                item_input_data.item_id,
            )

        except Exception as exc:  # noqa: BLE001
            workflow.logger.error(
                "Processing failed for item %s: %s",
                item_input_data.item_id,
                exc,
            )

            return {
                "status": "error",
                "item_id": item_input_data.item_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        else:
            return {
                "status": "success",
                "item_id": item_input_data.item_id,
            }


@workflow.defn
class SimilaritySearchWorkflow:
    """Workflow for processing similarity search queries.

    This workflow orchestrates the similarity search pipeline:
    1. Generate embedding for search query
    2. Find similar items using vector similarity
    3. Cache results for user retrieval
    4. Update search status to completed
    """

    @workflow.run
    async def run(self, search_request: SimilaritySearchRequest) -> dict[str, Any]:
        """Run the similarity search workflow.

        Args:
            search_request: The search request data including query and user info.

        Returns:
            dict: Search result with status and similar items.
        """
        workflow.logger.info(
            "Starting similarity search workflow for query '%s' by user %s",
            search_request.query,
            search_request.user_id,
        )

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
            maximum_attempts=3,
        )

        try:
            # Step 1: Generate embedding for search query
            workflow.logger.info(
                "Generating embedding for query: %s", search_request.query
            )
            search_results = await workflow.execute_activity(
                generate_search_embedding,
                args=[search_request],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            # Step 2: Save search results and update status
            workflow.logger.info(
                "Saving search results for search ID: %s", search_request.search_id
            )
            await workflow.execute_activity(
                save_search_results,
                args=[search_results],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

            workflow.logger.info(
                "Successfully completed similarity search for query '%s'",
                search_request.query,
            )

            return {
                "status": "success",
                "search_id": search_request.search_id,
                "query": search_request.query,
                "results_count": len(search_results.get("items", [])),
            }

        except Exception as exc:  # noqa: BLE001
            workflow.logger.error(
                "Similarity search failed for query '%s': %s",
                search_request.query,
                exc,
            )

            return {
                "status": "error",
                "search_id": search_request.search_id,
                "query": search_request.query,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }


@workflow.defn
class ItemPublishingWorkflow:
    """Workflow for publishing items with embedding generation.

    This workflow handles the publishing process:
    1. Generate embedding for the item content
    2. Save embedding to the item
    3. Mark item as published (active=True)
    4. Update item status to published
    """

    @workflow.run
    async def run(self, item_input_data: ItemProcessingRequest) -> dict[str, Any]:
        """Run the publishing workflow.

        Args:
            item_input_data: The item data for publishing.

        Returns:
            dict: Publishing result with status.
        """
        workflow.logger.info(
            "Starting publishing workflow for item %s",
            item_input_data.item_id,
        )

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
            maximum_attempts=3,
        )

        try:
            # Step 1: Generate embedding for the item
            workflow.logger.info(
                "Generating embedding for item %s", item_input_data.item_id
            )
            embedding_result = await workflow.execute_activity(
                generate_item_embedding,
                args=[item_input_data],
                start_to_close_timeout=timedelta(minutes=1),  # Reduced timeout
                retry_policy=retry_policy,
            )

            workflow.logger.info(
                "Successfully completed publishing for item %s - Result: %s",
                item_input_data.item_id,
                embedding_result,
            )

            return {
                "status": "success",
                "item_id": item_input_data.item_id,
                "embedding_created": embedding_result.get("embedding_created", False),
                "embedding_updated": embedding_result.get("embedding_updated", False),
                "embedding_dimensions": embedding_result.get("embedding_dimensions", 0),
                "previous_embedding_existed": embedding_result.get(
                    "previous_embedding_existed", False
                ),
            }

        except Exception as exc:  # noqa: BLE001
            workflow.logger.error(
                "Publishing failed for item %s: %s",
                item_input_data.item_id,
                exc,
            )

            # Try to update the item status to failed even if workflow fails
            try:
                # Import Django components inside the except block
                import os

                import django

                os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
                django.setup()

                from bubble.items.models import Item, ProcessingStatus

                item = Item.objects.get(id=item_input_data.item_id)
                item.publishing_status = ProcessingStatus.FAILED
                item.save(update_fields=["publishing_status"])
                workflow.logger.info(
                    "Updated item %s status to FAILED after workflow exception",
                    item_input_data.item_id,
                )
            except Exception as save_exc:
                workflow.logger.error(
                    "Could not update item %s status after workflow failure: %s",
                    item_input_data.item_id,
                    str(save_exc),
                )

            return {
                "status": "error",
                "item_id": item_input_data.item_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
