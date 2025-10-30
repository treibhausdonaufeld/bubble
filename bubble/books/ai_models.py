"""
AI extraction models for books app.
"""

from dataclasses import dataclass


@dataclass
class BookPhotoExtraction:
    """Model for book data extracted from photo using Gemini Vision."""

    isbn: str | None = None
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    year: str | None = None


@dataclass
class Book:
    """Complete book model for AI extraction workflow."""

    isbn: str | None = None
    title: str | None = None
    authors: str | None = None
    publisher: str | None = None
    published_year: str | None = None
    location: str | None = None
    description: str | None = None
    topic: str | None = None
    genre: str | None = None
    page_count: str | None = None
    language: str | None = None
    source: str | None = None
