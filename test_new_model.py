import sys

sys.path.append("/home/dev-user/.local/lib/python3.13/site-packages")

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django

django.setup()

from bubble.categories.models import ItemCategory
from bubble.items.models import Item
from bubble.items.services.embedding_service import EmbeddingService
from bubble.users.models import User

print("Testing new embedding service with mpnet model...")

# Test the service
service = EmbeddingService()
print(f"Model: {service.model}")
print(f"Embedding dimension: {service.model.get_sentence_embedding_dimension()}")

# Test embedding generation
test_text = "Gaming Laptop für Videobearbeitung"
embedding = service.generate_embedding(test_text)
print(
    f"Generated embedding for '{test_text}': {len(embedding) if embedding else 'Failed'} dimensions"
)

# Test with a real item
user, _ = User.objects.get_or_create(
    username="test_new_model", defaults={"email": "test@example.com"}
)

# Use existing category
existing_categories = list(ItemCategory.objects.all())
category = existing_categories[0] if existing_categories else None

# Create test item
item, created = Item.objects.get_or_create(
    name="Test Gaming Setup",
    user=user,
    defaults={
        "description": "Professioneller Gaming-Computer mit RTX 4080, 32GB RAM, ideal für 4K Gaming",
        "category": category,
        "price": 1500.00,
        "item_type": Item.ITEM_TYPE_FOR_SALE,
        "status": Item.STATUS_USED,
        "active": True,
    },
)

print(f"\nTesting with item: {item.name}")
item_embedding = service.generate_item_embedding(item)
if item_embedding:
    item.embedding = item_embedding
    item.save(update_fields=["embedding"])
    print("✓ Saved embedding for item (768 dimensions)")

    # Test similarity search
    from pgvector.django import CosineDistance

    query = "Computer für Gaming mit moderner Grafikkarte"
    query_embedding = service.generate_embedding(query)

    if query_embedding:
        similar_items = (
            Item.objects.filter(active=True, embedding__isnull=False)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:3]
        )

        print(f"\nSimilarity search for: '{query}'")
        for item in similar_items:
            print(f"- {item.name} (distance: {item.distance:.4f})")
    else:
        print("Failed to generate query embedding")
else:
    print("✗ Failed to generate item embedding")

print("\nTest completed!")
