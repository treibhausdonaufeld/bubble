import contextlib

import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

from .models import Author, Book, Genre, Publisher


class OpenLibraryService:
    BASE_URL = "https://openlibrary.org/api/books"

    def get_book_details(self, isbn: str):
        params = {
            "bibkeys": f"ISBN:{isbn}",
            "jscmd": "details",
            "format": "json",
        }
        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get(f"ISBN:{isbn}", {}).get("details", {})

    def update_book_from_isbn(self, book: Book, isbn: str | None = None):
        isbn_to_use = isbn or book.isbn
        if not isbn_to_use:
            return

        details = self.get_book_details(isbn_to_use)
        if not details:
            return

        book.isbn = isbn_to_use
        self._update_book_fields(book, details)
        self._update_related_fields(book, details)
        self._fetch_and_set_cover_image(book, details)

        book.save()

    def _update_book_fields(self, book: Book, details: dict):
        book.name = details.get("title", book.name)
        if "publish_date" in details:
            with contextlib.suppress(ValueError, IndexError):
                book.year = int(details["publish_date"].split()[-1])
        book.description = details.get("description", book.description)
        if details.get("languages"):
            lang_key = details["languages"][0]["key"]
            book.language = lang_key.split("/")[-1]

    def _update_related_fields(self, book: Book, details: dict):
        if "authors" in details:
            for author_data in details["authors"]:
                author, _ = Author.objects.get_or_create(name=author_data["name"])
                book.authors.add(author)

        if "publishers" in details:
            for publisher_name in details["publishers"]:
                publisher, _ = Publisher.objects.get_or_create(name=publisher_name)
                book.verlag = publisher
                break  # Assuming one publisher

        if "subjects" in details:
            for subject_data in details["subjects"]:
                genre, _ = Genre.objects.get_or_create(name=subject_data)
                book.genres.add(genre)

    def _fetch_and_set_cover_image(self, book: Book, details: dict):
        if book.images.exists():  # type: ignore  # noqa: PGH003
            return

        thumbnail_url = details.get("thumbnail_url")
        if not thumbnail_url and "covers" in details and details["covers"]:
            thumbnail_url = (
                f"https://covers.openlibrary.org/b/id/{details['covers'][0]}-L.jpg"
            )

        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url, timeout=10)
                response.raise_for_status()
                image_name = f"{slugify(book.name)}-cover.jpg"
                book.images.create(image=ContentFile(response.content, name=image_name))  # pyright: ignore[reportAttributeAccessIssue]
            except requests.RequestException:
                pass
