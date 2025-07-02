"""Temporal.io activities for item processing.

Activities in Temporal are the functions that perform the actual work.
They should be deterministic and idempotent when possible.
"""

import logging
import secrets
import time
from dataclasses import dataclass
from typing import Any

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class ImageProcessingResult:
    """Result of image processing activity."""

    title: str
    description: str
    confidence: float
    processing_time: float


@dataclass
class ProcessingError:
    """Error information for failed processing."""

    error_type: str
    message: str
    retry_count: int


@activity.defn
async def analyze_item_images(item_id: int) -> ImageProcessingResult:
    """Analyze uploaded images and generate suggestions.

    This activity simulates AI-powered image analysis.
    In production, this would call actual ML/AI services.

    Args:
        item_id: The ID of the item to analyze.

    Returns:
        ImageProcessingResult: Analysis results with suggestions.

    Raises:
        ValueError: If item not found or invalid.
        RuntimeError: If processing fails.
    """
    logger.info("Starting image analysis for item %s", item_id)

    try:
        # TODO: get image data an process it

        # Simulate processing time (2-5 seconds)
        processing_time = 2 + (secrets.randbelow(300) / 100)  # 2.0-4.99 seconds
        time.sleep(processing_time)  # noqa: ASYNC251

        # Generate suggestions based on images
        suggestions = _generate_ai_suggestions(item_id, 1)

        result = ImageProcessingResult(
            title=suggestions["title"],
            description=suggestions["description"],
            confidence=suggestions["confidence"],
            processing_time=processing_time,
        )
    except Exception as exc:
        logger.exception("Error analyzing images for item %s", item_id)
        error_msg = "Image analysis failed"
        raise RuntimeError(error_msg) from exc
    else:
        logger.info("Completed image analysis for item %s", item_id)
        return result


@activity.defn
async def send_processing_notification(
    item_id: int,
    user_id: int,
    suggestions: ImageProcessingResult,
) -> bool:
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
        "suggestions": {
            "title": suggestions.title,
            "description": suggestions.description,
            "confidence": suggestions.confidence,
        },
        "processing_time": suggestions.processing_time,
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
