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

    def __str__(self) -> str:
        return str(self.name)

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

    def __str__(self) -> str:
        return str(self.name)

    def natural_key(self):
        return (self.name,)

    def get_hierarchy(self) -> str:
        """Returns the full genre hierarchy path"""
        if self.parent_genre:
            return f"{self.parent_genre.get_hierarchy()} > {str(self.name)}"
        return str(self.name)


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

    def __str__(self) -> str:
        return str(self.name)

    def natural_key(self):
        return (self.name,)


class VerlagManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Verlag(models.Model):
    """Publisher model"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    objects = VerlagManager()

    class Meta:
        verbose_name = _("Publisher")
        verbose_name_plural = _("Publishers")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)

    def natural_key(self):
        return (self.name,)


class OrtManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Ort(models.Model):
    """Place/City model"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    objects = OrtManager()

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)

    def natural_key(self):
        return (self.name,)


class RegalManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Regal(models.Model):
    """Shelf model for book storage location"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    objects = RegalManager()

    class Meta:
        verbose_name = _("Shelf")
        verbose_name_plural = _("Shelves")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)

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
    OWNERSHIP_CHOICES = [
        ('library', _('Library')),
        ('user', _('User')),
    ]
    
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
    verlag = models.ForeignKey(
        Verlag,
        on_delete=models.SET_NULL,
        related_name="books",
        blank=True,
        null=True,
        help_text=_("Publisher")
    )
    ort = models.ForeignKey(
        Ort,
        on_delete=models.SET_NULL,
        related_name="books",
        blank=True,
        null=True,
        help_text=_("Place of publication")
    )
    topic = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Main topic or subject")
    )
    description = models.TextField(blank=True, help_text=_("Book description"))
    referenz = models.TextField(
        blank=True,
        help_text=_("References (multiple allowed)")
    )
    
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
    
    # Ownership and library fields
    ownership = models.CharField(
        max_length=20,
        choices=OWNERSHIP_CHOICES,
        default='user',
        help_text=_("Book ownership type")
    )
    abbreviation = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Library abbreviation (only if ownership is library)")
    )
    regal = models.ForeignKey(
        Regal,
        on_delete=models.SET_NULL,
        related_name="books",
        blank=True,
        null=True,
        help_text=_("Shelf location")
    )
    
    # Booking fields
    booked = models.BooleanField(
        default=False,
        help_text=_("Is the book currently booked?")
    )
    booked_till = models.DateField(
        blank=True,
        null=True,
        help_text=_("Booked until date (only if booked)")
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
        dimensions=1536,  # Using OpenAI text-embedding-3-small dimensions
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

    def __str__(self) -> str:
        return str(self.title) if self.title else f"Book {self.pk}"

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
            str(self.year) if self.year else "",
            self.verlag.name if self.verlag else "",
            self.ort.name if self.ort else "",
            self.get_genres_display(),
            self.topic or "",
            self.description or "",
            self.referenz or "",
            self.ownership or "",
            self.abbreviation or "",
            self.regal.name if self.regal else "",
        ]
        return " ".join(filter(None, content_parts))