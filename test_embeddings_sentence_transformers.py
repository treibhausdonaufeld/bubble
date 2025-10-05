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

# Initialize the model
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


def prepare_item_text(item: Item) -> str:
    """Prepare text from item fields for embedding."""
    parts = []

    if item.name:
        parts.append(f"Name: {item.name}")

    if item.description:
        parts.append(f"Description: {item.description}")

    if item.category:
        parts.append(f"Category: {item.category.name}")

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
    print("Testing Sentence Transformers Embedding Generation")
    print("=" * 80)

    # Get or create test user
    user, _ = User.objects.get_or_create(
        username="test_embeddings", defaults={"email": "test@example.com"}
    )

    # Get or create test categories
    electronics_cat, _ = ItemCategory.objects.get_or_create(
        name="Electronics", defaults={"parent_category": None}
    )

    sports_cat, _ = ItemCategory.objects.get_or_create(
        name="Sports", defaults={"parent_category": None}
    )

    kitchen_cat, _ = ItemCategory.objects.get_or_create(
        name="Kitchen", defaults={"parent_category": None}
    )

    # Create test items with embeddings (German content for multilingual model)
    test_items = [
        {
            "name": "Gaming Laptop ASUS ROG",
            "description": "Hochleistungs-Gaming-Laptop mit RTX 3080, 32GB RAM, perfekt für Gaming und Videobearbeitung",
            "category": electronics_cat,
        },
        {
            "name": "Office Laptop ThinkPad",
            "description": "Business-Laptop ideal für Büroarbeit, leicht, lange Akkulaufzeit, tolle Tastatur",
            "category": electronics_cat,
        },
        {
            "name": "Mountain Bike Trek",
            "description": "Professionelles Mountainbike, 29 Zoll Räder, Carbon-Rahmen, geeignet für Trails und Wettkämpfe",
            "category": sports_cat,
        },
        {
            "name": "Kaffeemaschine DeLonghi",
            "description": "Automatische Espressomaschine mit Milchaufschäumer, macht Cappuccino, Latte und Americano",
            "category": kitchen_cat,
        },
        {
            "name": "iPhone 13 Pro",
            "description": "Apple iPhone 13 Pro, 256GB, Space Grau, sehr guter Zustand, mit Originalverpackung",
            "category": electronics_cat,
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

    print("\n2. Model info:")
    print("- Model: paraphrase-multilingual-MiniLM-L12-v2")
    print(f"- Dimension: {model.get_sentence_embedding_dimension()}")
    print("- Supports German: Yes")

    print("\n3. Testing similarity search...")

    # Test queries in German
    queries = [
        "Ich brauche einen Laptop zum Spielen",
        "Suche etwas für die Büroarbeit",
        "Ich möchte zu Hause Kaffee machen",
        "Brauche Ausrüstung für Bergsport",
        "Suche ein Smartphone von Apple",
    ]

    for query in queries:
        find_similar_items(query)
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
