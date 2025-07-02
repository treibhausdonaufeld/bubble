"""Temporal.io workflows for item processing.

Workflows in Temporal orchestrate activities and handle the business logic.
They must be deterministic and use only Temporal APIs for side effects.
"""

import logging
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from bubble.items.temporal.temporal_activities import analyze_item_images
from bubble.items.temporal.temporal_activities import send_processing_notification

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
    async def run(self, item_id: int, user_id: int) -> dict[str, Any]:
        """Run the image processing workflow.

        Args:
            item_id: The ID of the item to process.
            user_id: The ID of the user who owns the item.

        Returns:
            dict: Processing result with status and suggestions.
        """
        workflow.logger.info("Starting image processing workflow for item %s", item_id)

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        try:
            # Step 1: Analyze images
            workflow.logger.info("Analyzing images for item %s", item_id)
            suggestions = await workflow.execute_activity(
                analyze_item_images,
                args=[item_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            # Step 3: Send notification (best effort, don't fail workflow if this fails)
            await workflow.execute_activity(
                send_processing_notification,
                args=[item_id, user_id, suggestions],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )

            workflow.logger.info(
                "Successfully completed processing for item %s",
                item_id,
            )

        except Exception as exc:  # noqa: BLE001
            workflow.logger.error("Processing failed for item %s: %s", item_id, exc)

            return {
                "status": "error",
                "item_id": item_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        else:
            return {
                "status": "success",
                "item_id": item_id,
                "suggested_data": {
                    "title": suggestions.title,
                    "description": suggestions.description,
                    "confidence": suggestions.confidence,
                    "processing_time": suggestions.processing_time,
                },
            }
