import sys

sys.path.append("/home/dev-user/.local/lib/python3.13/site-packages")

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django

django.setup()

import openai
from pgvector.django import CosineDistance

from bubble.categories.models import ItemCategory
from bubble.items.models import Item
from bubble.users.models import User

# Configure OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

print(f"OpenAI API Key exists: {bool(openai.api_key)}")

# Quick test
if openai.api_key:
    try:
        # Create a test embedding
        response = openai.embeddings.create(
            model="text-embedding-3-small", input="Test embedding generation"
        )
        print(
            f"✓ Successfully generated embedding with {len(response.data[0].embedding)} dimensions"
        )

        # Get or create test user
        user, _ = User.objects.get_or_create(
            username="test_embeddings", defaults={"email": "test@example.com"}
        )

        # Get or create test category
        category, _ = ItemCategory.objects.get_or_create(
            name="Test Category", defaults={"parent_category": None}
        )

        # Create a test item
        item, created = Item.objects.get_or_create(
            name="Test Laptop",
            user=user,
            defaults={
                "description": "A test laptop for embedding generation",
                "category": category,
                "price": 100.00,
                "item_type": Item.ITEM_TYPE_FOR_SALE,
                "status": Item.STATUS_USED,
            },
        )

        # Generate and save embedding
        text = f"Name: {item.name} | Description: {item.description} | Category: {category.name}"
        embedding_response = openai.embeddings.create(
            model="text-embedding-3-small", input=text
        )

        item.embedding = embedding_response.data[0].embedding
        item.save()

        print(f"✓ Saved embedding for item: {item.name}")

        # Test similarity search
        query = "Looking for a laptop"
        query_response = openai.embeddings.create(
            model="text-embedding-3-small", input=query
        )
        query_embedding = query_response.data[0].embedding

        # Find similar items
        similar_items = (
            Item.objects.filter(embedding__isnull=False)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:5]
        )

        print(f"\nItems similar to '{query}':")
        for item in similar_items:
            print(f"- {item.name} (distance: {item.distance:.4f})")

    except Exception as e:
        print(f"Error: {e}")
else:
    print("Please set OPENAI_API_KEY in environment variables")
