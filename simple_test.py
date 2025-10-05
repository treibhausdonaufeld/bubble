import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

print("Testing find_similar_items method...")
try:
    from bubble.items.services.embedding_service import EmbeddingService

    service = EmbeddingService()
    results = service.find_similar_items("test query", limit=3)
    print(f"✓ Method works! Found {len(results)} results")
    print("✓ Similarity search is now functional")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
