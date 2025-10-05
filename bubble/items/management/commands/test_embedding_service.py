"""
Management command to test the embedding service.
"""

from django.core.management.base import BaseCommand

from bubble.items.models import Item
from bubble.items.services.embedding_service import EmbeddingService


class Command(BaseCommand):
    help = "Test the embedding service with a sample item"

    def add_arguments(self, parser):
        parser.add_argument(
            "--item-id",
            type=int,
            help="ID of item to test embedding generation for",
        )

    def handle(self, *args, **options):
        item_id = options.get("item_id")

        if item_id:
            try:
                item = Item.objects.get(id=item_id)
                self.stdout.write(
                    f'Testing embedding generation for item {item_id}: "{item.name}"'
                )
            except Item.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Item with ID {item_id} not found"))
                return
        else:
            # Get the first item as a test
            item = Item.objects.first()
            if not item:
                self.stdout.write(self.style.ERROR("No items found in database"))
                return
            self.stdout.write(
                f'Testing embedding generation for first item: "{item.name}"'
            )

        try:
            # Test the embedding service
            self.stdout.write("Initializing embedding service...")
            service = EmbeddingService()

            self.stdout.write("Preparing item text...")
            text = service.prepare_item_text(item)
            self.stdout.write(f"Prepared text: {text}")

            self.stdout.write("Generating embedding...")
            embedding = service.generate_item_embedding(item)

            if embedding:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Successfully generated embedding with {len(embedding)} dimensions"
                    )
                )

                # Test similarity search
                self.stdout.write("Testing similarity search...")
                similar_items = service.find_similar_items(item.name or "test", limit=3)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Found {len(similar_items)} similar items")
                )

            else:
                self.stdout.write(self.style.ERROR("✗ Failed to generate embedding"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e!s}"))
            import traceback

            self.stdout.write(traceback.format_exc())
