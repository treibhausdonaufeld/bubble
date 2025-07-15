import os

import openai
from django.core.management.base import BaseCommand
from pgvector.django import CosineDistance

from bubble.categories.models import ItemCategory
from bubble.items.models import Item
from bubble.users.models import User


class Command(BaseCommand):
    help = "Test embedding generation and similarity search"

    def handle(self, *args, **options):
        # Configure OpenAI
        openai.api_key = os.environ.get("OPENAI_API_KEY", "")

        if not openai.api_key:
            self.stdout.write(
                self.style.ERROR("OPENAI_API_KEY not found in environment")
            )
            return

        self.stdout.write(
            self.style.SUCCESS("Testing Embedding Generation and Similarity Search")
        )
        self.stdout.write("=" * 80)

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

        self.stdout.write("\n1. Creating test items and generating embeddings...")
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
                text = self.prepare_item_text(item)
                embedding = self.generate_embedding(text)

                if embedding:
                    item.embedding = embedding
                    item.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Generated embedding for: {item.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to generate embedding for: {item.name}"
                        )
                    )

        self.stdout.write("\n2. Testing similarity search...")

        # Test queries
        queries = [
            "I need a laptop for gaming",
            "Looking for something for office work",
            "I want to make coffee at home",
            "Need equipment for mountain sports",
        ]

        for query in queries:
            self.find_similar_items(query)
            input("\nPress Enter to continue...")

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for given text using OpenAI API."""
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating embedding: {e}"))
            return None

    def prepare_item_text(self, item: Item) -> str:
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

    def find_similar_items(self, query_text: str, limit: int = 5):
        """Find items similar to the query text."""
        # Generate embedding for query
        query_embedding = self.generate_embedding(query_text)
        if not query_embedding:
            self.stdout.write(self.style.ERROR("Failed to generate query embedding"))
            return

        # Find similar items using pgvector
        similar_items = (
            Item.objects.filter(embedding__isnull=False)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:limit]
        )

        self.stdout.write(f"\nTop {limit} items similar to '{query_text}':")
        self.stdout.write("-" * 80)

        for item in similar_items:
            self.stdout.write(f"Item: {item.name}")
            self.stdout.write(f"Description: {item.description[:100]}...")
            self.stdout.write(
                f"Category: {item.category.name if item.category else 'None'}"
            )
            self.stdout.write(f"Distance: {item.distance:.4f}")
            self.stdout.write("-" * 40)
