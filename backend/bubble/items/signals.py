"""Signals for automatic embedding generation."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from bubble.items.embeddings import generate_item_embedding
from bubble.items.models import Item, ItemEmbedding


@receiver(post_save, sender=Item)
def update_item_embedding(sender, instance, created, **kwargs):
    """
    Automatically generate and update embeddings when an Item is saved.

    This signal runs after an Item is saved and checks if the name or
    description has changed. If so, it generates a new embedding vector.

    Args:
        sender: The model class (Item).
        instance: The actual Item instance being saved.
        created: Boolean indicating if this is a new instance.
        **kwargs: Additional keyword arguments from the signal.
    """
    # Skip if we're in a raw save (e.g., during migrations or fixtures)
    if kwargs.get("raw", False):
        return

    # Check if name or description has changed
    should_update = False

    if created:
        # Always generate embedding for new items
        should_update = True
    else:
        # Check if name or description changed
        try:
            old_instance = Item.objects.get(pk=instance.pk)
            if (
                old_instance.name != instance.name
                or old_instance.description != instance.description
            ):
                should_update = True
        except Item.DoesNotExist:
            should_update = True

    if should_update:
        # Generate and save the embedding
        vector_embedding = generate_item_embedding(instance)
        if vector_embedding is not None:
            # Update without triggering the signal again
            ItemEmbedding.objects.update_or_create(
                item=instance, defaults={"vector": vector_embedding}
            )
