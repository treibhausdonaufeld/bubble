"""
Celery tasks for books app.
"""
import logging

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_book_embedding(self, book_id):
    """
    Generate embedding for a book in the background.
    """
    try:
        from bubble.books.models import Book
        from bubble.books.services.embeddings import get_embeddings_service
        
        book = Book.objects.get(id=book_id)
        embeddings_service = get_embeddings_service()
        
        success = embeddings_service.update_book_embedding(book)
        
        if success:
            logger.info(f"Successfully generated embedding for book {book_id}: {book.title}")
            return f"Embedding generated for book {book_id}"
        else:
            logger.error(f"Failed to generate embedding for book {book_id}")
            raise Exception(f"Failed to generate embedding for book {book_id}")
            
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        raise Exception(f"Book {book_id} not found")
    except Exception as exc:
        logger.error(f"Error generating embedding for book {book_id}: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task
def batch_generate_embeddings(book_ids=None):
    """
    Generate embeddings for multiple books.
    If book_ids is None, generate for all books without embeddings.
    """
    from bubble.books.models import Book
    
    if book_ids is None:
        # Get all books without embeddings
        books_without_embeddings = Book.objects.filter(
            active=True,
            embedding__isnull=True
        ).values_list('id', flat=True)
        book_ids = list(books_without_embeddings)
    
    logger.info(f"Starting batch embedding generation for {len(book_ids)} books")
    
    results = []
    for book_id in book_ids:
        try:
            result = generate_book_embedding.delay(book_id)
            results.append(result.id)
        except Exception as e:
            logger.error(f"Failed to queue embedding task for book {book_id}: {e}")
    
    logger.info(f"Queued {len(results)} embedding tasks")
    return results


@shared_task
def update_related_book_embeddings(author_id=None, genre_id=None):
    """
    Update embeddings for books when related objects (authors/genres) change.
    """
    from bubble.books.models import Book
    
    queryset = Book.objects.filter(active=True)
    
    if author_id:
        queryset = queryset.filter(authors__id=author_id)
    if genre_id:
        queryset = queryset.filter(genres__id=genre_id)
    
    book_ids = list(queryset.values_list('id', flat=True))
    
    if book_ids:
        logger.info(f"Updating embeddings for {len(book_ids)} books affected by related object changes")
        return batch_generate_embeddings.delay(book_ids)
    
    return "No books to update"