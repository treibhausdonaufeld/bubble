import sys

sys.path.append("/home/dev-user/.local/lib/python3.13/site-packages")

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django

django.setup()

from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

from bubble.categories.models import ItemCategory
from bubble.items.models import Item
from bubble.users.models import User

print("Loading Sentence Transformer model...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print(
    f"✓ Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}"
)


def generate_embedding(text: str):
    """Generate embedding for given text using Sentence Transformers."""
    try:
        embedding = model.encode(text)
        return embedding.tolist()  # Convert numpy array to list
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def main():
    print("Testing Sentence Transformers Embedding Generation")
    print("=" * 80)

    # Get or create test user
    user, _ = User.objects.get_or_create(
        username="test_embeddings", defaults={"email": "test@example.com"}
    )

    # Use existing category or None
    existing_categories = list(ItemCategory.objects.all())
    category = existing_categories[0] if existing_categories else None

    print(f"Using category: {category}")

    # Create a simple test item
    item, created = Item.objects.get_or_create(
        name="Test Laptop für Gaming",
        user=user,
        defaults={
            "description": "Ein leistungsstarker Gaming-Laptop mit moderner Grafikkarte",
            "category": category,
            "price": 100.00,
            "item_type": Item.ITEM_TYPE_FOR_SALE,
            "status": Item.STATUS_USED,
        },
    )

    # Generate and save embedding
    text = f"Name: {item.name} | Description: {item.description}"
    if category:
        text += f" | Category: {category.name}"

    print(f"Generating embedding for text: {text}")

    embedding = generate_embedding(text)
    if embedding:
        item.embedding = embedding
        item.save()
        print(f"✓ Saved embedding for item: {item.name}")
        print(f"✓ Embedding dimensions: {len(embedding)}")

        # Test similarity search
        query = "Gaming Computer für Spiele"
        print(f"\nTesting similarity search with query: '{query}'")

        query_embedding = generate_embedding(query)
        if query_embedding:
            # Find similar items
            similar_items = (
                Item.objects.filter(embedding__isnull=False)
                .annotate(distance=CosineDistance("embedding", query_embedding))
                .order_by("distance")[:3]
            )

            print("\nSimilar items:")
            for item in similar_items:
                print(f"- {item.name} (distance: {item.distance:.4f})")
        else:
            print("Failed to generate query embedding")
    else:
        print("Failed to generate embedding")


if __name__ == "__main__":
    main()
