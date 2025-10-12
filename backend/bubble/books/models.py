import uuid

from django.db import models
from django.utils.translation import gettext as _
from simple_history.models import HistoricalRecords

from bubble.items.models import Item, ItemManager


class Author(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Author")
        verbose_name_plural = _("Authors")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Genre(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_genre = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subgenres",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Genre")
        verbose_name_plural = _("Genres")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)

    def get_hierarchy(self) -> str:
        """Returns the full genre hierarchy path"""
        if self.parent_genre:
            return f"{self.parent_genre.get_hierarchy()} > {self.name!s}"
        return str(self.name)


class Publisher(models.Model):
    """Publisher model"""

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Publisher")
        verbose_name_plural = _("Publishers")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Shelf(models.Model):
    """Shelf model for book storage location"""

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Shelf")
        verbose_name_plural = _("Shelves")
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Book(Item):
    isbn = models.CharField(max_length=13, blank=True)

    authors = models.ManyToManyField(
        Author, related_name="books", help_text=_("Book authors")
    )
    language = models.CharField(
        max_length=50, blank=True, help_text=_("Language of the book")
    )
    year = models.PositiveIntegerField(
        blank=True, null=True, help_text=_("Publication year")
    )
    verlag = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        related_name="books",
        blank=True,
        null=True,
        help_text=_("Publisher"),
    )
    topic = models.CharField(
        max_length=255, blank=True, help_text=_("Main topic or subject")
    )
    genres = models.ManyToManyField(
        Genre, related_name="books", blank=True, help_text=_("Book genres")
    )

    # location management
    shelf = models.ForeignKey(
        Shelf,
        on_delete=models.SET_NULL,
        related_name="books",
        blank=True,
        null=True,
        help_text=_("Shelf location"),
    )

    history = HistoricalRecords()

    objects = ItemManager()
