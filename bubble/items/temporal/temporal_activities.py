"""Temporal.io activities for item processing.

Activities in Temporal are the functions that perform the actual work.
They should be deterministic and idempotent when possible.
"""

import base64
import json
import logging
import re
from dataclasses import dataclass

import requests
from temporalio import activity

from .anthropic_client import call_model

logger = logging.getLogger(__name__)


PROMPT_RETURN_FORMAT = (
    "Antworte ausschließlich mit validem JSON in folgendem Format: "
    "{\n"
    '  "title": "Kurzer prägnanter Titel für den Gegenstand",\n'
    '  "description": "Detaillierte Beschreibung des Gegenstands '
    'und seines Zustands",\n'
    '  "category": "Hauptkategorie des Gegenstands"\n'
    '  "price": "Vorgeschlagener Verkaufspreis in Euro"\n'
    "}"
)


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
    price: str | None = None


@dataclass
class ProcessingError:
    """Error information for failed processing."""

    error_type: str
    message: str
    retry_count: int


@dataclass
class SimilaritySearchRequest:
    """Request data for similarity search activity."""

    search_id: str
    query: str
    user_id: int
    token: str
    base_url: str


def fetch_categories(base_url: str, token: str) -> list[str]:
    """Fetch item categories from the API."""
    categories_url = f"{base_url}/api/categories/"
    headers = {"Authorization": f"Token {token}"}

    categories = []

    while categories_url:
        response = requests.get(categories_url, headers=headers, timeout=30)
        response.raise_for_status()

        categories_data = response.json()
        categories.extend([cat["name"] for cat in categories_data["results"]])

        # Get next page URL if it exists
        categories_url = categories_data.get("next")

    return categories


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
    image_url = f"{image_input.base_url}/api/images/{image_input.image_id}/preview/"
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

    categories_string = ", ".join(
        fetch_categories(image_input.base_url, image_input.token)
    )

    prompt_instruction = (
        "Analysiere dieses Bild und gib eine strukturierte Antwort im JSON-Format. "
        "Fokussiere auf: Art des Gegenstands, Zustand, bemerkenswerte Eigenschaften. "
        "Gib einen Preisvorschlage für den Verkauf des Artikels. "
        f"Die Kategorie soll aus dieser Liste gewählt werden: {categories_string}"
    ) + PROMPT_RETURN_FORMAT

    logger.info("Prompt instruction: %s", prompt_instruction)

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
        image_input.price = parsed_response.get("price")

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
            "vorschlag für die felder im JSON-Format zurück. "
        ) + PROMPT_RETURN_FORMAT
        response_text = call_model(
            prompt=prompt_instruction,
            extra_prompt={
                "type": "text",
                "text": "\n".join(
                    [
                        f"Title: {result.title}\n"
                        f"Description: {result.description}\n"
                        f"Category: {result.category}"
                        f"Price: {result.price}"
                        for result in image_results
                    ],
                ),
            },
        )
        parsed_response = json.loads(response_text)
        result.title = parsed_response.get("title")
        result.description = parsed_response.get("description")
        result.category = parsed_response.get("category")
        result.price = parsed_response.get("price")

    return result


@activity.defn
def save_item_suggestions(item_result: ItemImageResult) -> bool:
    """Save item data via api to the backend"""

    item_url = f"{item_result.base_url}/api/items/{item_result.item_id}/"
    logger.info("Item API URL: %s", item_url)

    # fetch image data from rest api with authentication token
    headers = {"Authorization": f"Token {item_result.token}"}

    # extract only the numeric data from item_result.price with a regex
    price_match = re.search(r"\d+(\.\d{1,2})?", item_result.price or "0.00")
    if price_match:
        item_result.price = price_match.group(0)

    # Put the item data to the API
    item_data = {
        "processing_status": 2,  # completed
        "name": item_result.title,
        "description": item_result.description,
        "category": item_result.category,
        "price": item_result.price,
    }
    response = requests.put(item_url, headers=headers, json=item_data, timeout=30)

    response.raise_for_status()

    logger.info("Item data saved: %s", item_result)
    return True


@activity.defn
def generate_search_embedding(search_request: SimilaritySearchRequest) -> dict:
    """Generate embedding for search query and find similar items."""
    logger.info("Generating embedding for search query: %s", search_request.query)

    # Call the Django API to perform the search
    search_url = f"{search_request.base_url}/items/api/similarity-search/"
    headers = {"Authorization": f"Token {search_request.token}"}

    search_data = {
        "query": search_request.query,
        "search_id": search_request.search_id,
    }

    try:
        response = requests.post(
            search_url, headers=headers, json=search_data, timeout=60
        )
        response.raise_for_status()

        search_results = response.json()
        logger.info(
            "Generated embedding and found %d similar items",
            len(search_results.get("items", [])),
        )

        return {
            "search_id": search_request.search_id,
            "query": search_request.query,
            "items": search_results.get("items", []),
            "status": "completed",
        }

    except Exception as e:
        logger.error("Error in generate_search_embedding: %s", str(e))
        return {
            "search_id": search_request.search_id,
            "query": search_request.query,
            "items": [],
            "status": "failed",
            "error": str(e),
        }


@activity.defn
def save_search_results(search_results: dict) -> bool:
    """Save search results to database."""
    logger.info("Saving search results for search ID: %s", search_results["search_id"])

    try:
        # Import Django components
        import os
        from datetime import datetime

        import django

        # Set up Django environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
        django.setup()

        from bubble.items.models import SearchStatus, SimilaritySearch

        # Update the search record
        search_obj = SimilaritySearch.objects.get(search_id=search_results["search_id"])
        search_obj.results = search_results.get("items", [])
        search_obj.results_count = len(search_results.get("items", []))
        search_obj.date_completed = datetime.now()

        if search_results.get("status") == "failed":
            search_obj.status = SearchStatus.FAILED
            search_obj.error_message = search_results.get("error", "Unknown error")
        else:
            search_obj.status = SearchStatus.COMPLETED

        search_obj.save()

        logger.info(
            "Search results saved successfully for search ID: %s",
            search_results["search_id"],
        )
        return True

    except Exception as e:
        logger.error("Error saving search results: %s", str(e))
        return False


@activity.defn
def generate_item_embedding(item_request: ItemProcessingRequest) -> dict:
    """Generate and save embedding for an item during publishing."""
    logger.info("Generating embedding for item %s", item_request.item_id)

    result = {
        "item_id": item_request.item_id,
        "embedding_created": False,
        "embedding_updated": False,
        "previous_embedding_existed": False,
        "embedding_dimensions": 0,
        "status": "pending",
    }

    try:
        # Import Django components
        import os
        import time

        import django

        # Set up Django environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
        django.setup()

        from bubble.items.models import Item, ProcessingStatus
        from bubble.items.services.embedding_service import EmbeddingService

        # Get the item
        item = Item.objects.get(id=item_request.item_id)

        # Check if embedding already exists
        old_embedding = item.embedding
        result["previous_embedding_existed"] = old_embedding is not None

        # Add a small delay to make the processing visible
        time.sleep(1)  # 1 second delay to show processing status

        # Generate new embedding with timeout handling
        try:
            embedding_service = EmbeddingService()
            new_embedding = embedding_service.generate_item_embedding(item)

            if new_embedding is None:
                logger.error(
                    "EmbeddingService returned None for item %s", item_request.item_id
                )
                item.publishing_status = ProcessingStatus.FAILED
                item.save(update_fields=["publishing_status"])
                result["status"] = "failed"
                result["error"] = "Embedding service returned None"
                return result

        except Exception as embedding_error:
            logger.error(
                "Error in embedding service for item %s: %s",
                item_request.item_id,
                str(embedding_error),
            )
            item.publishing_status = ProcessingStatus.FAILED
            item.save(update_fields=["publishing_status"])
            result["status"] = "failed"
            result["error"] = f"Embedding service error: {embedding_error!s}"
            return result

        if new_embedding:
            result["embedding_dimensions"] = len(new_embedding)

            # Save the new embedding
            item.embedding = new_embedding
            item.publishing_status = ProcessingStatus.COMPLETED
            item.save(update_fields=["embedding", "publishing_status"])

            result["embedding_created"] = not result["previous_embedding_existed"]
            result["embedding_updated"] = result["previous_embedding_existed"]
            result["status"] = "completed"

            logger.info(
                "Successfully processed embedding for item %s - Created: %s, Updated: %s",
                item_request.item_id,
                result["embedding_created"],
                result["embedding_updated"],
            )
            return result
        logger.warning("No embedding generated for item %s", item_request.item_id)
        item.publishing_status = ProcessingStatus.FAILED
        item.save(update_fields=["publishing_status"])
        result["status"] = "failed"
        return result

    except Exception as e:
        logger.error(
            "Error generating embedding for item %s: %s", item_request.item_id, str(e)
        )
        result["status"] = "error"
        result["error"] = str(e)
        try:
            # Update status to failed on exception
            from bubble.items.models import Item, ProcessingStatus

            item = Item.objects.get(id=item_request.item_id)
            item.publishing_status = ProcessingStatus.FAILED
            item.save(update_fields=["publishing_status"])
            logger.info(
                "Updated item %s publishing status to FAILED", item_request.item_id
            )
        except Exception as save_error:
            logger.error(
                "Could not update item %s status to FAILED: %s",
                item_request.item_id,
                str(save_error),
            )
        return result
