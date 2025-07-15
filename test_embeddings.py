#!/usr/bin/env python
"""
Test script for embedding generation and similarity search.
Run with: python test_embeddings.py
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from pgvector.django import CosineDistance

from bubble.categories.models import ItemCategory
from bubble.items.models import Item
from bubble.users.models import User

# Configure OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY", "")


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for given text using OpenAI API."""
    try:
        response = openai.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def prepare_item_text(item: Item) -> str:
    """Prepare text from item fields for embedding."""
    parts = []

    if item.name:
        parts.append(f"Name: {item.name}")

    if item.description:
        parts.append(f"Description: {item.description}")

    if item.category:
        parts.append(f"Category: {item.category.name}")

    parts.append(f"Type: {item.get_item_type_display()}")
    parts.append(f"Condition: {item.get_status_display()}")

    return " | ".join(parts)


def find_similar_items(query_text: str, limit: int = 5):
    """Find items similar to the query text."""
    # Generate embedding for query
    query_embedding = generate_embedding(query_text)
    if not query_embedding:
        print("Failed to generate query embedding")
        return

    # Find similar items using pgvector
    similar_items = (
        Item.objects.filter(embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:limit]
    )

    print(f"\nTop {limit} items similar to '{query_text}':")
    print("-" * 80)

    for item in similar_items:
        print(f"Item: {item.name}")
        print(f"Description: {item.description[:100]}...")
        print(f"Category: {item.category.name if item.category else 'None'}")
        print(f"Distance: {item.distance:.4f}")
        print("-" * 40)


def main():
    """Main test function."""
    print("Testing Embedding Generation and Similarity Search")
    print("=" * 80)

    # Get or create test user
    user, _ = User.objects.get_or_create(
        username="test_embeddings", defaults={"email": "test@example.com"}
    )

    # Get or create test category
    category, _ = ItemCategory.objects.get_or_create(
        name="Electronics", defaults={"parent_category": None}
    )

    # Create test items with embeddings
    test_items = [
        {
            "name": "Gaming Laptop ASUS ROG",
            "description": "High-performance gaming laptop with RTX 3080, 32GB RAM, perfect for gaming and video editing",
            "category": category,
        },
        {
            "name": "Office Laptop ThinkPad",
            "description": "Business laptop ideal for office work, lightweight, long battery life, great keyboard",
            "category": category,
        },
        {
            "name": "Mountain Bike Trek",
            "description": "Professional mountain bike, 29 inch wheels, carbon frame, suitable for trails and competitions",
            "category": ItemCategory.objects.get_or_create(name="Sports")[0],
        },
        {
            "name": "Coffee Machine DeLonghi",
            "description": "Automatic espresso machine with milk frother, makes cappuccino, latte, and americano",
            "category": ItemCategory.objects.get_or_create(name="Kitchen")[0],
        },
    ]

    print("\n1. Creating test items and generating embeddings...")
    for item_data in test_items:
        item, created = Item.objects.get_or_create(
            name=item_data["name"],
            user=user,
            defaults={
                "description": item_data["description"],
                "category": item_data["category"],
                "price": 100.00,
                "item_type": Item.ITEM_TYPE_FOR_SALE,
                "status": Item.STATUS_USED,
            },
        )

        if created or not item.embedding:
            # Generate embedding
            text = prepare_item_text(item)
            embedding = generate_embedding(text)

            if embedding:
                item.embedding = embedding
                item.save()
                print(f"✓ Generated embedding for: {item.name}")
            else:
                print(f"✗ Failed to generate embedding for: {item.name}")

    print("\n2. Testing similarity search...")

    # Test queries
    queries = [
        "I need a laptop for gaming",
        "Looking for something for office work",
        "I want to make coffee at home",
        "Need equipment for mountain sports",
    ]

    for query in queries:
        find_similar_items(query)
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
