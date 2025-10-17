import contextlib

import isbnlib
import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify
from rest_framework.exceptions import APIException, ValidationError

from .models import Author, Book, Publisher


class ISBNValidationError(ValidationError):
    """Raised when ISBN is invalid or cannot be validated."""


class ISBNMetadataNotFoundError(APIException):
    """Raised when no metadata can be found for the given ISBN."""

    status_code = 404
    default_detail = "No metadata found for the given ISBN."
    default_code = "metadata_not_found"


class OpenLibraryService:
    """Service for fetching book metadata using ISBN."""

    def get_book_details(self, isbn: str):
        """
        Fetch book details from various metadata providers using isbnlib.

        Returns a dictionary with book metadata.

        Raises:
            ISBNValidationError: If ISBN is invalid or cannot be validated.
            ISBNMetadataNotFoundError: If no metadata can be found for the ISBN.
        """
        # Clean the ISBN (remove hyphens, spaces)
        clean_isbn = isbnlib.canonical(isbn)
        if not clean_isbn:
            msg = f"Invalid ISBN format: {isbn}"
            raise ISBNValidationError(msg)

        # Use isbnlib.meta to fetch metadata from multiple providers
        # This tries multiple services (Google Books, Open Library, etc.)
        metadata = isbnlib.meta(clean_isbn, service="default")
        if not metadata:
            msg = f"No metadata found for ISBN: {isbn}"
            raise ISBNMetadataNotFoundError(msg)

        return metadata, clean_isbn

    def update_book_from_isbn(self, book: Book, isbn: str | None = None):
        isbn_to_use = isbn or book.isbn
        if not isbn_to_use:
            return

        details, book.isbn = self.get_book_details(isbn_to_use)
        book.metadata = details

        self._update_book_fields(book, details)
        self._update_related_fields(book, details)
        self._fetch_and_set_cover_image(book, details)

        book.save()

    def _update_book_fields(self, book: Book, details: dict):
        """
        Update book fields from isbnlib metadata.

        isbnlib.meta returns a dict with keys:
        - 'Title': book title
        - 'Authors': list of author names
        - 'Publisher': publisher name
        - 'Year': publication year
        - 'ISBN-13': ISBN-13 number
        - 'Language': language code
        """
        book.name = details.get("Title", book.name)

        if "Year" in details:
            with contextlib.suppress(ValueError, TypeError):
                book.year = int(details["Year"])

        # isbnlib doesn't provide description, keep existing
        # book.description stays unchanged

        if "Language" in details:
            book.language = details["Language"]

    def _update_related_fields(self, book: Book, details: dict):
        """Update related models (authors, publisher, genres) from metadata."""
        # Handle authors
        if details.get("Authors"):
            for author_name in details["Authors"]:
                author, _ = Author.objects.get_or_create(name=author_name)
                book.authors.add(author)

        # Handle publisher
        if details.get("Publisher"):
            publisher, _ = Publisher.objects.get_or_create(name=details["Publisher"])
            book.verlag = publisher

        # isbnlib doesn't provide subjects/genres, so we skip that
        # Genres would need to be added manually or from another source

    def _fetch_and_set_cover_image(self, book: Book, details: dict):
        """Fetch and set cover image using isbnlib."""
        if book.images.exists():  # type: ignore  # noqa: PGH003
            return

        # Get ISBN-13 from details or use the book's ISBN
        isbn_13 = details.get("ISBN-13") or book.isbn
        if not isbn_13:
            return

        # Clean the ISBN
        clean_isbn = isbnlib.canonical(isbn_13)
        if not clean_isbn:
            return

        # Try to get cover URL from isbnlib
        # isbnlib.cover returns a dict with different sizes:
        # 'smallThumbnail', 'thumbnail', etc.
        try:
            cover_urls = isbnlib.cover(clean_isbn)
            if not cover_urls or not isinstance(cover_urls, dict):
                return

            # Try to get the best available cover image
            thumbnail_url = (
                cover_urls.get("thumbnail")
                or cover_urls.get("smallThumbnail")
                or next(iter(cover_urls.values()), None)
            )

            if thumbnail_url:
                response = requests.get(thumbnail_url, timeout=10)
                response.raise_for_status()
                image_name = f"{slugify(book.name)}-cover.jpg"
                book.images.create(  # pyright: ignore[reportAttributeAccessIssue]
                    image=ContentFile(response.content, name=image_name)
                )
        except (requests.RequestException, isbnlib.ISBNLibException):
            # Silently fail if cover cannot be fetched
            pass
