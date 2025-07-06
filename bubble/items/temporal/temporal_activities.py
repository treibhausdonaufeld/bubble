"""Temporal.io activities for item processing.

Activities in Temporal are the functions that perform the actual work.
They should be deterministic and idempotent when possible.
"""

import logging
import secrets
from dataclasses import dataclass
from typing import Any

import httpx
from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class ItemProcessingRequest:
    """Request data for item processing activity."""

    item_id: int
    user_id: int
    token: str
    base_url: str


@dataclass
class ItemImagesResult:
    """Result of image processing activity."""

    item_id: int
    image_id: int
    token: str
    base_url: str
    description: str | None = None


@dataclass
class ItemResult:
    """Result of item description summarization."""

    title: str | None = None
    description: str | None = None
    category: str | None = None


@dataclass
class ProcessingError:
    """Error information for failed processing."""

    error_type: str
    message: str
    retry_count: int


@activity.defn
async def fetch_item_images(
    input_data: ItemProcessingRequest,
) -> list[ItemImagesResult]:
    logger.info("Start to fetch images for item %s", input_data.item_id)

    # fetch image data from rest api with authentication token
    headers = {"Authorization": f"Token {input_data.token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{input_data.base_url}/api/images/?item={input_data.item_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        images_data = response.json()

    if not images_data:
        logger.warning("No images found for item %s", input_data.item_id)
        return []

    return [
        ItemImagesResult(
            item_id=input_data.item_id,
            image_id=image["id"],
            token=input_data.token,
            base_url=input_data.base_url,
        )
        for image in images_data
    ]


@activity.defn
async def analyze_image(
    image_input: ItemImagesResult,
) -> ItemImagesResult:
    """Analyze a single image and generate AI suggestions."""

    image_input.description = "Dummy description for image analysis"
    return image_input


@activity.defn
async def summarize_image_suggestions(
    image_input: list[ItemImagesResult],
) -> ItemResult:
    """Summarize suggestions from multiple images into a single description."""

    # Generate dummy AI suggestions based on the number of images
    item_id = image_input[0].item_id
    image_count = len(image_input)
    suggestions = _generate_ai_suggestions(item_id, image_count)

    logger.info(
        "Generated suggestions for item %s: %s",
        item_id,
        suggestions,
    )

    result: ItemResult = ItemResult(
        title=suggestions["title"],
        description=suggestions["description"],
        category="General",  # Placeholder category
    )

    return result


@activity.defn
async def send_processing_notification(item_id: int, user_id: int) -> bool:
    """Send notification when processing is complete.

    Args:
        item_id: The ID of the processed item.
        user_id: The ID of the user to notify.
        suggestions: The processing results.

    Returns:
        bool: True if notification was sent successfully.
    """
    logger.info(
        "Sending processing notification for item %s to user %s",
        item_id,
        user_id,
    )

    # Placeholder for WebSocket notification
    # In a real implementation, you would use Django Channels
    notification_data = {
        "item_id": item_id,
        "user_id": user_id,
    }

    logger.info("Would send notification: %s", notification_data)
    return True


def _generate_ai_suggestions(item: Any, image_count: int) -> dict[str, Any]:
    """Generate dummy AI suggestions based on uploaded images.

    Args:
        item: The Item instance to generate suggestions for.
        image_count: Number of images uploaded.

    Returns:
        dict: Dictionary containing suggested title, description, and metadata.
    """
    # Dummy title suggestions
    titles = [
        "Vintage Collectible Item",
        "Beautiful Handcrafted Piece",
        "Quality Home Decor",
        "Unique Antique Find",
        "Modern Design Item",
        "Artisan Made Creation",
        "Rare Vintage Piece",
        "Stylish Home Accessory",
    ]

    # Dummy descriptions
    descriptions = [
        (
            "This beautiful item is in excellent condition and would make "
            "a great addition to any home. Features unique design elements "
            "and quality craftsmanship."
        ),
        (
            "Vintage piece with character and charm. Shows normal signs of "
            "age but remains functional and attractive. Perfect for collectors."
        ),
        (
            "Modern design meets functionality in this stylish piece. Clean "
            "lines and quality materials make this a standout item."
        ),
        (
            "Handcrafted with attention to detail. This unique piece shows "
            "the artisan's skill and would be perfect for someone who "
            "appreciates quality work."
        ),
        (
            "Rare find in good condition. This item has interesting history "
            "and would appeal to enthusiasts and collectors alike."
        ),
    ]

    # Add image-specific context
    image_context = ""
    if image_count > 1:
        image_context = (
            f" Multiple images show different angles and "
            f"details of this {image_count}-piece item."
        )
    elif image_count == 1:
        image_context = " Single clear image shows the item's excellent condition."

    selected_description = (
        descriptions[secrets.randbelow(len(descriptions))] + image_context
    )

    return {
        "title": titles[secrets.randbelow(len(titles))],
        "description": selected_description,
        "confidence": 0.7 + (secrets.randbelow(25) / 100),  # 0.7-0.94
    }
