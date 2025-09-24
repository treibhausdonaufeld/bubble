import uuid
from pathlib import Path
from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _
from pgvector.django import VectorField, CosineDistance

from config.settings.base import AUTH_USER_MODEL


class AuthorManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True)
    
    objects = AuthorManager()

    class Meta:
        verbose_name = _("Author")
        verbose_name_plural = _("Authors")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class GenreManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_genre = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subgenres",
        blank=True,
        null=True,
    )

    objects = GenreManager()

    class Meta:
        verbose_name = _("Genre")
        verbose_name_plural = _("Genres")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def get_hierarchy(self):
        """Returns the full genre hierarchy path"""
        if self.parent_genre:
            return f"{self.parent_genre.get_hierarchy()} > {self.name}"
        return self.name


class LocationManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Location(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    objects = LocationManager()

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class BookManager(models.Manager):
    def for_user(self, user) -> models.QuerySet:
        """Return a queryset filtered by user permissions."""
        q = models.Q(active=True, internal=False)
        if user.is_authenticated:
            # allow also own books of this user
            q |= models.Q(user=user)
            if hasattr(user, "profile") and user.profile.internal:
                # allow all active books for internal users
                q |= models.Q(active=True)
        return self.filter(q)

    def search_similar(self, query_embedding: List[float], limit: int = 10):
        """Search for books similar to the given embedding vector."""
        return self.annotate(
            similarity=CosineDistance('embedding', query_embedding)
        ).order_by('similarity')[:limit]


class Book(models.Model):
    active = models.BooleanField(default=True)
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="books",
    )
    
    # Core book fields
    title = models.CharField(max_length=500, help_text=_("Book title"))
    authors = models.ManyToManyField(
        Author,
        related_name="books",
        help_text=_("Book authors")
    )
    year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_("Publication year")
    )
    topic = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Main topic or subject")
    )
    description = models.TextField(blank=True, help_text=_("Book description"))
    
    # Relationships
    genres = models.ManyToManyField(
        Genre,
        related_name="books",
        blank=True,
        help_text=_("Book genres")
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        related_name="books",
        blank=True,
        null=True,
        help_text=_("Book location")
    )
    
    # Image field
    image = models.ImageField(
        upload_to='books/covers/',
        blank=True,
        null=True,
        help_text=_("Book cover image")
    )
    
    # System fields
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Unique identifier for the book"),
    )
    internal = models.BooleanField(
        default=False,
        help_text=_("Internal book, not for public display"),
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    # Vector field for semantic search
    embedding = VectorField(
        dimensions=384,  # Using SentenceTransformers all-MiniLM-L6-v2 dimensions
        null=True,
        blank=True,
        help_text=_("Vector embedding for semantic search")
    )

    # Custom manager
    objects = BookManager()

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")
        ordering = ["-date_created"]

    def __str__(self):
        return self.title or f"Book {self.pk}"

    def is_ready_for_display(self):
        """Check if book has minimum required fields to be displayed."""
        return bool(self.title and self.authors.exists())

    def get_authors_display(self):
        """Return comma-separated list of authors."""
        return ", ".join([author.name for author in self.authors.all()])

    def get_genres_display(self):
        """Return comma-separated list of genres."""
        return ", ".join([genre.name for genre in self.genres.all()])

    def get_content_for_embedding(self):
        """Generate text content for creating embeddings."""
        content_parts = [
            self.title or "",
            self.get_authors_display(),
            self.get_genres_display(),
            self.topic or "",
            self.description or "",
        ]
        return " ".join(filter(None, content_parts))