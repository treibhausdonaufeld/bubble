"""Temporal.io activities for item processing.

Activities in Temporal are the functions that perform the actual work.
They should be deterministic and idempotent when possible.
"""

import base64
import json
import logging
from dataclasses import dataclass

import requests
from temporalio import activity

from .anthropic_client import call_model

logger = logging.getLogger(__name__)


@dataclass
class ItemProcessingRequest:
    """Request data for item processing activity."""

    item_id: int
    user_id: int
    token: str
    base_url: str


@dataclass
class ItemImageResult:
    """Result of image processing activity."""

    item_id: int
    image_id: int
    token: str
    base_url: str
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
def fetch_item_images(
    input_data: ItemProcessingRequest,
) -> list[ItemImageResult]:
    logger.info("Start to fetch images for item %s", input_data.item_id)

    image_url = f"{input_data.base_url}/api/images/?item={input_data.item_id}"
    logger.info("Image API URL: %s", image_url)

    # fetch image data from rest api with authentication token
    headers = {"Authorization": f"Token {input_data.token}"}
    response = requests.get(image_url, headers=headers, timeout=30)
    response.raise_for_status()

    images_data = response.json()

    logger.info("Image data: %s", images_data)

    if not images_data:
        logger.warning("No images found for item %s", input_data.item_id)
        return []

    return [
        ItemImageResult(
            item_id=input_data.item_id,
            image_id=image["id"],
            token=input_data.token,
            base_url=input_data.base_url,
        )
        for image in images_data["results"]
    ]


@activity.defn
def analyze_image(
    image_input: ItemImageResult,
) -> ItemImageResult:
    """Analyze a single image and generate AI suggestions."""

    # fetch image from api
    image_url = f"{image_input.base_url}/api/images/{image_input.image_id}/original/"
    logger.info("Fetching image from URL: %s", image_url)

    headers = {"Authorization": f"Token {image_input.token}"}
    response = requests.get(image_url, headers=headers, timeout=30)
    response.raise_for_status()

    # image data is binary, fetch it as bytes
    image_data = response.content

    # Convert image to base64 for Anthropic API
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # Determine image format from content type or file extension
    content_type = response.headers.get("content-type", "image/jpeg")
    logger.info("Image content type: %s", content_type)

    prompt_instruction = (
        "Analysiere dieses Bild und gib eine strukturierte Antwort im JSON-Format. "
        "Fokussiere auf: Art des Gegenstands, Zustand, bemerkenswerte Eigenschaften. "
        "Antworte ausschließlich mit validem JSON in folgendem Format:\n"
        "{\n"
        '  "title": "Kurzer prägnanter Titel für den Gegenstand",\n'
        '  "description": "Detaillierte Beschreibung des Gegenstands '
        'und seines Zustands",\n'
        '  "category": "Hauptkategorie des Gegenstands"\n'
        "}"
    )

    response_text = call_model(
        prompt=prompt_instruction,
        extra_prompt={
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": content_type,
                "data": image_base64,
            },
        },
    )

    logger.info("AI response: %s", response_text)

    try:
        parsed_response = json.loads(response_text)
        image_input.title = parsed_response.get("title")
        image_input.description = parsed_response.get("description")
        image_input.category = parsed_response.get("category")

        logger.info(
            "AI analysis completed for image %s: %s",
            image_input.image_id,
            parsed_response,
        )

    except json.JSONDecodeError:
        logger.exception("Failed to parse response: %s", response_text)
        image_input.description = "Unable to parse AI response"

    return image_input


@activity.defn
def summarize_image_suggestions(
    image_results: list[ItemImageResult],
) -> ItemImageResult:
    """Summarize suggestions from multiple images into a single description."""

    result = image_results[0]

    if len(image_results) > 1:
        prompt_instruction = (
            "Fasse all diese beschreibungen zusammen und gib genau einen "
            "vorschlag für titel, beschreibung und kategorie für das objekt. "
            "Antworte ausschließlich mit validem JSON in folgendem Format:\n"
            "{\n"
            '  "title": "Kurzer prägnanter Titel für den Gegenstand",\n'
            '  "description": "Detaillierte Beschreibung des Gegenstands '
            'und seines Zustands",\n'
            '  "category": "Hauptkategorie des Gegenstands"\n'
            "}"
        )
        response_text = call_model(
            prompt=prompt_instruction,
            extra_prompt={
                "type": "text",
                "text": "\n".join(
                    [
                        f"Title: {result.title}\n"
                        f"Description: {result.description}\n"
                        f"Category: {result.category}"
                        for result in image_results
                    ],
                ),
            },
        )
        parsed_response = json.loads(response_text)
        result.title = parsed_response.get("title")
        result.description = parsed_response.get("description")
        result.category = parsed_response.get("category")

    return result


@activity.defn
def save_item_suggestions(item_result: ItemImageResult) -> bool:
    """Save item data via api to the backend"""

    item_url = f"{item_result.base_url}/api/items/{item_result.item_id}/"
    logger.info("Item API URL: %s", item_url)

    # fetch image data from rest api with authentication token
    headers = {"Authorization": f"Token {item_result.token}"}

    # Put the item data to the API
    item_data = {
        "processing_status": 2,  # completed
        "title": item_result.title,
        "description": item_result.description
        + "\n\nKategorie: "
        + item_result.category,
    }
    response = requests.put(item_url, headers=headers, json=item_data, timeout=30)

    response.raise_for_status()

    logger.info("Item data saved: %s", item_result)
    return True
