"""
Signals for books app to handle embedding generation.
"""
import logging

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import Book, Author, Genre
from .tasks import generate_book_embedding, update_related_book_embeddings

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Book)
def book_post_save(sender, instance, created, **kwargs):
    """
    Generate embedding when a book is created or updated.
    """
    # Only generate embedding if the book is active and has required content
    if instance.active and instance.title:
        try:
            # Generate embedding in background
            generate_book_embedding.delay(instance.id)
            logger.info(f"Queued embedding generation for book {instance.id}: {instance.title}")
        except Exception as e:
            logger.error(f"Failed to queue embedding generation for book {instance.id}: {e}")


@receiver(m2m_changed, sender=Book.authors.through)
def book_authors_changed(sender, instance, action, pk_set, **kwargs):
    """
    Regenerate embedding when book authors change.
    """
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.active:
        try:
            generate_book_embedding.delay(instance.id)
            logger.info(f"Queued embedding update for book {instance.id} due to author changes")
        except Exception as e:
            logger.error(f"Failed to queue embedding update for book {instance.id}: {e}")


@receiver(m2m_changed, sender=Book.genres.through)
def book_genres_changed(sender, instance, action, pk_set, **kwargs):
    """
    Regenerate embedding when book genres change.
    """
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.active:
        try:
            generate_book_embedding.delay(instance.id)
            logger.info(f"Queued embedding update for book {instance.id} due to genre changes")
        except Exception as e:
            logger.error(f"Failed to queue embedding update for book {instance.id}: {e}")


@receiver(post_save, sender=Author)
def author_post_save(sender, instance, created, **kwargs):
    """
    Update embeddings for books when author information changes.
    """
    if not created:  # Only for updates, not creation
        try:
            update_related_book_embeddings.delay(author_id=instance.id)
            logger.info(f"Queued embedding updates for books by author {instance.id}: {instance.name}")
        except Exception as e:
            logger.error(f"Failed to queue embedding updates for author {instance.id}: {e}")


@receiver(post_save, sender=Genre)
def genre_post_save(sender, instance, created, **kwargs):
    """
    Update embeddings for books when genre information changes.
    """
    if not created:  # Only for updates, not creation
        try:
            update_related_book_embeddings.delay(genre_id=instance.id)
            logger.info(f"Queued embedding updates for books in genre {instance.id}: {instance.name}")
        except Exception as e:
            logger.error(f"Failed to queue embedding updates for genre {instance.id}: {e}")