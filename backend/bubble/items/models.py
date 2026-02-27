import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from guardian.shortcuts import assign_perm, get_objects_for_user
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToCover, ResizeToFill
from pgvector.django import VectorField
from simple_history.models import HistoricalRecords

from bubble.items.embeddings import get_embedding_model
from config.settings.base import AUTH_USER_MODEL

money_defaults = {
    "max_digits": 10,
    "decimal_places": 2,
}


class ConditionType(models.IntegerChoices):
    NEW = 0, _("New")
    USED = 1, _("Used")
    BROKEN = 2, _("Broken")


class ItemStatus(models.IntegerChoices):
    DRAFT = 0, _("Draft")
    PROCESSING = 1, _("Processing")
    AVAILABLE = 2, _("Available")
    RESERVED = 3, _("Reserved")
    RENTED = 4, _("Rented")
    SOLD = 5, _("Sold")

    @classmethod
    def published(cls):
        return (cls.AVAILABLE, cls.RESERVED, cls.RENTED, cls.SOLD)


class RentalPeriodType(models.TextChoices):
    HOURLY = "h", _("Hourly")
    DAILY = "d", _("Daily")
    WEEKLY = "w", _("Weekly")


class VisibilityType(models.IntegerChoices):
    PUBLIC = 0, _("Public")
    AUTHENTICATED = 1, _("Authenticated")
    SPECIFIC = 2, _("Specific")
    PRIVATE = 3, _("Private")


class CategoryType(models.TextChoices):
    BOOKS = "books", _("Books")
    CLOTHING = "clothing", _("Clothing")
    ELECTRONICS = "electronics", _("Electronics")
    FURNITURE = "furniture", _("Furniture")
    GARDEN = "garden", _("Garden")
    KITCHEN = "kitchen", _("Kitchen")
    OTHER = "other", _("Other")
    ROOMS = "rooms", _("Rooms")
    SPORTS = "sports", _("Sports")
    TOOLS = "tools", _("Tools")
    TOYS = "toys", _("Toys")
    VEHICLES = "vehicles", _("Vehicles")


class ItemManager(models.Manager):
    def published(self) -> models.QuerySet:
        """Return a queryset of published items."""
        return self.filter(status__in=ItemStatus.published())

    def get_for_user(self, user) -> models.QuerySet:
        """Return a queryset filtered by user permissions."""
        items_with_change_permission = get_objects_for_user(
            user,
            f"{self.model._meta.app_label}.change_{self.model._meta.model_name}",  # noqa: SLF001
            accept_global_perms=False,
        )
        return self.filter(pk__in=items_with_change_permission)

    def semantic_search(self, query: str, limit: int = 10) -> models.QuerySet:
        """
        Perform semantic search on items using embeddings.

        Args:
            query: The search query text.
            limit: Maximum number of results to return (default: 10).

        Returns:
            QuerySet ordered by semantic similarity (most similar first).
        """

        # Generate embedding for the query
        model = get_embedding_model()
        query_embedding = model.encode(query, convert_to_numpy=True).tolist()

        # Use cosine distance for similarity (lower distance = more similar)
        # Filter out items without embeddings
        return (
            self.filter(embedding__isnull=False)
            .order_by(models.F("embedding__vector").cosine_distance(query_embedding))
            .all()[:limit]
        )


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        choices=CategoryType,
        help_text=_("Category of the item"),
    )
    name = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    internal = models.BooleanField(
        default=False,
        help_text=_("Internal item, not for public display"),
    )
    display_contact = models.BooleanField(
        default=False,
        help_text=_("Display your contact information public"),
    )
    sale_price = MoneyField(
        **money_defaults,
        blank=True,
        null=True,
        default_currency=settings.DEFAULT_CURRENCY,
    )
    rental_price = MoneyField(
        **money_defaults,
        blank=True,
        null=True,
        help_text=_("Price per hour for rental items"),
        default_currency=settings.DEFAULT_CURRENCY,
    )

    rental_period = models.CharField(
        max_length=1,
        blank=True,
        choices=RentalPeriodType,
        default=RentalPeriodType.HOURLY,
    )
    rental_self_service = models.BooleanField(
        default=False,
        help_text=_("Allow self-service rental without owner approval"),
    )
    rental_open_end = models.BooleanField(
        default=False,
        help_text=_("Allow open-ended rentals without a return date"),
    )

    payment_enabled = models.BooleanField(
        default=False,
        help_text=_("Enable payment via internal payment system"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    condition = models.IntegerField(
        choices=ConditionType,
        default=ConditionType.USED,
        help_text=_("Condition of the item"),
    )
    active = models.BooleanField(default=True)

    status = models.IntegerField(
        choices=ItemStatus,
        default=ItemStatus.DRAFT,
    )

    visibility = models.IntegerField(
        choices=VisibilityType,
        default=VisibilityType.AUTHENTICATED,
        help_text=_(
            "Who can see this item: Public (everyone), "
            "Authenticated (logged-in users), "
            "Specific (selected users/groups), "
            "or Private (owner and co-owners only)."
        ),
    )

    # enable history tracking
    history = HistoricalRecords()

    # Custom manager
    objects = ItemManager()

    # Add class constants for easy access
    CONDITION_CHOICES = ConditionType.choices

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(sale_price__isnull=True)
                    | models.Q(rental_price__isnull=True)
                ),
                name="items_sale_or_rental_price_not_both",
            )
        ]

    def __str__(self):
        return f"{self.pk} - {self.name}" or f"Item {self.pk}"

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            queryset = self._meta.model.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            counter = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

        if self.user:
            # give owner full object permissions on instance
            app_label = self._meta.model._meta.app_label  # noqa: SLF001
            model_name = self._meta.model._meta.model_name  # noqa: SLF001
            assign_perm(f"{app_label}.view_{model_name}", self.user, obj=self)
            assign_perm(f"{app_label}.change_{model_name}", self.user, obj=self)
            assign_perm(f"{app_label}.delete_{model_name}", self.user, obj=self)

    def is_ready_for_display(self):
        """Check if item has minimum required fields to be displayed."""
        return bool(self.name and self.category)

    def get_first_image(self):
        """Return the first image of the item based on ordering."""
        return self.images.order_by("ordering").first()


class ItemUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Item, on_delete=models.CASCADE)


class ItemGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Item, on_delete=models.CASCADE)


class ItemEmbedding(models.Model):
    item = models.OneToOneField(
        Item, on_delete=models.CASCADE, related_name="embedding", primary_key=True
    )
    vector = VectorField(
        dimensions=384,
        null=True,
        blank=True,
        help_text=_("Embedding vector for semantic search"),
    )

    def __str__(self):
        return f"Embedding for {self.item.name} ({self.item.id})"


def upload_to_item_images(instance: "Image", filename: str):
    extension: str = Path(filename).suffix or ".jpg"
    item_creation_datestr = instance.item.created_at.strftime("%Y/%m/%d")
    item_prefix: str = f"items/{item_creation_datestr}/{instance.item.id}"
    return f"{item_prefix}/{str(uuid.uuid4())[0:8]}/original{extension}"


class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original = models.ImageField(upload_to=upload_to_item_images, max_length=255)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    ordering = models.IntegerField(default=0)

    thumbnail = ImageSpecField(
        source="original",
        processors=[ResizeToFill(300, 200)],
        format="JPEG",
        options={"quality": 88},
    )
    preview = ImageSpecField(
        source="original",
        processors=[ResizeToCover(1200, 1200)],
        format="JPEG",
        options={"quality": 88},
    )

    class Meta:
        ordering = ["item", "ordering"]

    def __str__(self):
        return f"Image for {self.item.name} ({self.filename})"

    @property
    def filename(self):
        """Return the filename of the original image."""
        return self.original.name.split("/")[-1]

    def _get_temp_path(self, suffix: str) -> str | None:
        """Return the path where the image should be stored."""
        folder = f"temp/{suffix}/{str(self.item.id)[0:4]}/{self.pk}"
        return f"{folder}/{suffix}.jpg"

    def get_preview_path(self) -> str | None:
        """Return the path where the preview image should be stored."""
        if not self.original:
            return None
        return self._get_temp_path("preview")

    def get_thumbnail_path(self) -> str | None:
        """Return the path where the thumbnail image should be stored."""
        if not self.original:
            return None
        return self._get_temp_path("thumbnail")
