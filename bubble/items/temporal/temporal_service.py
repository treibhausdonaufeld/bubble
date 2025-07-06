"""Temporal.io client and service utilities for the items app.

This module provides a centralized way to interact with Temporal workflows
and manages the Temporal client connection.
"""

import logging
from typing import Any
from uuid import uuid4

from django.conf import settings
from temporalio.client import Client, WorkflowHandle
from temporalio.common import RetryPolicy

from bubble.items.temporal.temporal_activities import ItemProcessingRequest
from bubble.items.temporal.temporal_workflows import ItemProcessingWorkflow

logger = logging.getLogger(__name__)


class TemporalService:
    """Service class for managing Temporal workflow interactions."""

    _client: Client | None = None

    @classmethod
    async def get_client(cls) -> Client:
        """Get or create the Temporal client.

        Returns:
            Client: The Temporal client instance.
        """
        if cls._client is None:
            temporal_address = getattr(settings, "TEMPORAL_ADDRESS", "localhost:7233")
            cls._client = await Client.connect(temporal_address)
            logger.info("Connected to Temporal server at %s", temporal_address)

        return cls._client

    @classmethod
    async def start_item_processing(
        cls,
        input_data: ItemProcessingRequest,
    ) -> WorkflowHandle[ItemProcessingWorkflow, dict[str, Any]]:
        """Start image processing workflow for an item.

        Args:
            item_id: The ID of the item to process.
            user_id: The ID of the user who owns the item.
            task_queue: The task queue to use.

        Returns:
            WorkflowHandle: Handle to the started workflow.
        """
        task_queue: str = settings.TEMPORAL_TASK_QUEUE
        client = await cls.get_client()

        workflow_id = f"process-item-{input_data.item_id}-{uuid4().hex[:8]}"

        logger.info("Starting item processing workflow for item %s", input_data.item_id)

        handle = await client.start_workflow(
            ItemProcessingWorkflow.run,
            args=[input_data],
            id=workflow_id,
            task_queue=task_queue,
            retry_policy=RetryPolicy(maximum_attempts=1),  # Workflow-level retry
        )

        logger.info("Started workflow %s for item %s", workflow_id, input_data.item_id)
        return handle

    @classmethod
    async def get_workflow_result(
        cls,
        workflow_id: str,
        result_type: type = dict,
    ) -> Any:
        """Get the result of a completed workflow.

        Args:
            workflow_id: The ID of the workflow.
            result_type: The expected result type.

        Returns:
            Any: The workflow result.
        """
        client = await cls.get_client()

        handle = client.get_workflow_handle(workflow_id, result_type=result_type)
        result = await handle.result()

        logger.info("Retrieved result for workflow %s", workflow_id)
        return result

    @classmethod
    async def cancel_workflow(cls, workflow_id: str) -> bool:
        """Cancel a running workflow.

        Args:
            workflow_id: The ID of the workflow to cancel.

        Returns:
            bool: True if cancellation was successful.
        """
        try:
            client = await cls.get_client()
            handle = client.get_workflow_handle(workflow_id)
            await handle.cancel()

            logger.info("Cancelled workflow %s", workflow_id)
        except Exception:
            logger.exception("Failed to cancel workflow %s", workflow_id)
            return False
        else:
            return True

    @classmethod
    async def list_workflows(
        cls,
        query: str = "WorkflowType='ItemImageProcessingWorkflow'",
    ) -> list:
        """List workflows matching the given query.

        Args:
            query: The Temporal SQL query to filter workflows.

        Returns:
            list: List of workflow execution information.
        """
        client = await cls.get_client()

        workflows = [
            {
                "id": workflow.id,
                "type": workflow.workflow_type,
                "status": workflow.status,
                "start_time": workflow.start_time,
                "close_time": workflow.close_time,
            }
            async for workflow in client.list_workflows(query)
        ]

        logger.info("Found %d workflows matching query: %s", len(workflows), query)
        return workflows


# Convenience functions for common operations


async def start_item_processing(input_data: ItemProcessingRequest) -> str:
    """Start image processing for an item.

    Args:
        item_id: The ID of the item to process.
        user_id: The ID of the user who owns the item.

    Returns:
        str: The workflow ID.
    """
    handle = await TemporalService.start_item_processing(input_data)
    return handle.id


async def get_processing_result(workflow_id: str) -> dict:
    """Get the result of a processing workflow.

    Args:
        workflow_id: The ID of the workflow.

    Returns:
        dict: The processing result.
    """
    return await TemporalService.get_workflow_result(workflow_id)


async def cancel_processing(workflow_id: str) -> bool:
    """Cancel a processing workflow.

    Args:
        workflow_id: The ID of the workflow to cancel.

    Returns:
        bool: True if cancellation was successful.
    """
    return await TemporalService.cancel_workflow(workflow_id)
