"""Temporal.io worker for the items app.

This module sets up and runs the Temporal worker that will execute
activities and workflows for item processing.
"""

import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from temporalio.client import Client
from temporalio.worker import Worker

from bubble.items.temporal.temporal_activities import (
    analyze_image,
    fetch_item_images,
    send_processing_notification,
    summarize_image_suggestions,
)
from bubble.items.temporal.temporal_workflows import ItemProcessingWorkflow

logger = logging.getLogger(__name__)


class TemporalWorker:
    """Temporal worker for item processing tasks."""

    def __init__(
        self,
        temporal_address: str = "localhost:7233",
        task_queue: str = "",
        max_concurrent_activities: int = 10,
        max_concurrent_workflows: int = 5,
    ):
        """Initialize the Temporal worker.

        Args:
            temporal_address: Address of the Temporal server.
            task_queue: Task queue to listen on.
            max_concurrent_activities: Maximum concurrent activities.
            max_concurrent_workflows: Maximum concurrent workflows.
        """
        self.temporal_address = temporal_address
        self.task_queue = task_queue or settings.TEMPORAL_TASK_QUEUE
        self.max_concurrent_activities = max_concurrent_activities
        self.max_concurrent_workflows = max_concurrent_workflows
        self.client = None
        self.worker = None

    async def start(self):
        """Start the Temporal worker."""
        logger.info("Starting Temporal worker...")

        # Connect to Temporal server
        self.client = await Client.connect(self.temporal_address)
        logger.info("Connected to Temporal server at %s", self.temporal_address)

        # Create worker with activities and workflows
        with ThreadPoolExecutor(max_workers=self.max_concurrent_activities) as executor:
            self.worker = Worker(
                self.client,
                task_queue=self.task_queue,
                activities=[
                    fetch_item_images,
                    send_processing_notification,
                    analyze_image,
                    summarize_image_suggestions,
                ],
                workflows=[
                    ItemProcessingWorkflow,
                ],
                max_concurrent_activities=self.max_concurrent_activities,
                max_concurrent_workflow_tasks=self.max_concurrent_workflows,
                activity_executor=executor,
            )

        logger.info("Worker created for task queue '%s'", self.task_queue)

        # Start the worker
        logger.info("Starting worker execution...")
        await self.worker.run()

    async def stop(self):
        """Stop the Temporal worker."""
        if self.worker:
            logger.info("Stopping Temporal worker...")
            await self.worker.shutdown()

        logger.info("Temporal worker stopped")


async def run_worker():
    """Run the Temporal worker with proper error handling."""
    worker = TemporalWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception:
        logger.exception("Worker error")
        raise
    finally:
        await worker.stop()


def main():
    """Main entry point for the worker."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("temporal_worker.log"),
        ],
    )

    logger.info("Starting Temporal worker for items app...")

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception:
        logger.exception("Fatal worker error")
        sys.exit(1)


if __name__ == "__main__":
    main()
