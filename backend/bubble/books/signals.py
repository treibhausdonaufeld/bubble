"""Signals for the books app."""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from bubble.items.models import CategoryType, Item

from .models import Book


@receiver(post_save, sender=Item)
def promote_item_to_book(sender, instance, created, **kwargs):
    """
    Automatically promote an Item to a Book when category is 'books'.

    This allows items to be created as regular Items and automatically
    become Books when the category is set to 'books'.
    """
    # Skip if this is already a Book (to avoid recursion)
    if isinstance(instance, Book):
        return

    # Only promote if category is 'books'
    if instance.category != CategoryType.BOOKS:
        # If it was previously a Book but category changed, we could demote here
        # but for now we'll leave it as a Book (data preservation)
        return

    # Check if a Book entry already exists for this Item
    try:
        Book.objects.get(item_ptr_id=instance.pk)
    except Book.DoesNotExist:
        # Promote the Item to a Book
        with transaction.atomic():
            # Create a Book instance that points to this Item
            book = Book(item_ptr_id=instance.pk)
            # Copy all fields from Item to Book (they share the same database row)
            book.__dict__.update(instance.__dict__)
            book.save()


@receiver(post_save, sender=Item)
def demote_item_book(sender, instance, created, **kwargs):
    """
    Automatically demote a Book to a regular Item when category is changed from 'books'.
    """
    # Only proceed if this Item is a Book
    if not isinstance(instance, Book):
        return

    # If category is still 'books', no action needed
    if instance.category == CategoryType.BOOKS:
        return

    # Delete the book instance but keep the Item
    try:
        book = Book.objects.get(item_ptr_id=instance.pk)
        book.delete()
    except Book.DoesNotExist:
        pass
