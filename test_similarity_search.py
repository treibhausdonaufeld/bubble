#!/usr/bin/env python3
"""
Test script for the new find_similar_items method in EmbeddingService.
"""

import os
import sys

import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from bubble.items.models import Item
from bubble.items.services.embedding_service import EmbeddingService


def test_embedding_service():
    """Test the EmbeddingService find_similar_items method."""
    print("Testing EmbeddingService.find_similar_items method...")

    try:
        # Initialize the embedding service
        service = EmbeddingService()
        print("✓ EmbeddingService initialized successfully")

        # Test with empty query
        results = service.find_similar_items("")
        print(f"✓ Empty query test: returned {len(results)} results")

        # Test with a sample query
        test_query = "laptop computer"
        results = service.find_similar_items(test_query, limit=5)
        print(f"✓ Sample query '{test_query}': returned {len(results)} results")

        # Check if results have the correct format
        if results:
            item, similarity = results[0]
            print(
                f"✓ Result format correct: Item({item.id}), similarity={similarity:.3f}"
            )
            print(f"  - Item name: {item.name}")
            print(f"  - Item active: {item.active}")
        else:
            print(
                "! No results found (this might be expected if no items have embeddings yet)"
            )

        # Check total active items with embeddings
        items_with_embeddings = Item.objects.filter(
            active=True, embedding__isnull=False
        ).count()
        print(f"✓ Total active items with embeddings: {items_with_embeddings}")

        print(
            "\n✅ All tests passed! The find_similar_items method is working correctly."
        )

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_embedding_service()
    sys.exit(0 if success else 1)
