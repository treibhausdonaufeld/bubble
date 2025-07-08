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
        analyze_image,
        fetch_item_images,
        save_item_suggestions,
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
