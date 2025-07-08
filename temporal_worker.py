#!/usr/bin/env python

"""Temporal.io worker for the items app.

This module sets up and runs the Temporal worker that will execute
activities and workflows for item processing.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from bubble.items.temporal.temporal_activities import (
    analyze_image,
    fetch_item_images,
    save_item_suggestions,
    summarize_image_suggestions,
)
from bubble.items.temporal.temporal_workflows import ItemProcessingWorkflow
from config.settings.temporal import (
    TEMPORAL_ADDRESS,
    TEMPORAL_LOG_LEVEL,
    TEMPORAL_MAX_CONCURRENT_ACTIVITIES,
    TEMPORAL_NAMESPACE,
    TEMPORAL_TASK_QUEUE,
)

logging.basicConfig(
    level=TEMPORAL_LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def run_worker():
    # Create client connected to server at the given address
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)

    with ThreadPoolExecutor(max_workers=TEMPORAL_MAX_CONCURRENT_ACTIVITIES) as executor:
        worker = Worker(
            client,
            task_queue=TEMPORAL_TASK_QUEUE,
            activities=[
                fetch_item_images,
                save_item_suggestions,
                analyze_image,
                summarize_image_suggestions,
            ],
            workflows=[
                ItemProcessingWorkflow,
            ],
            activity_executor=executor,
        )
        await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
