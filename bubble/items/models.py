import uuid
from decimal import Decimal
from pathlib import Path

from django.db import models
from django.utils.translation import gettext_lazy as _

from config.settings.base import AUTH_USER_MODEL


class ConditionType(models.IntegerChoices):
    NEW = 0, _("New")
    USED = 1, _("Used")
    BROKEN = 2, _("Broken")


class ItemType(models.IntegerChoices):
    FOR_SALE = 0, _("For Sale")
    RENT = 1, _("Rent")
    BOTH = 2, _("Both")


class StatusType(models.IntegerChoices):
    DRAFT = 0, _("Draft")
    PROCESSING = 1, _("Processing")
    AVAILABLE = 2, _("Available")
    RESERVED = 3, _("Reserved")
    RENTED = 4, _("Rented")
    SOLD = 5, _("Sold")


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
    def for_user(self, user) -> models.QuerySet:
        """Return a queryset filtered by user permissions."""
        q = models.Q(status=StatusType.AVAILABLE)
        if user.is_authenticated:
            # allow also own items of this user
            q |= models.Q(user=user)
            if hasattr(user, "profile") and user.profile.internal:
                # allow all active items for internal users
                q |= models.Q(active=True)
        return self.filter(q)


class Item(models.Model):
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
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Unique identifier for the item"),
    )
    name = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, blank=True)
    description = models.TextField(blank=True)
    internal = models.BooleanField(
        default=False,
        help_text=_("Internal item, not for public display"),
    )
    display_contact = models.BooleanField(
        default=False,
        help_text=_("Display your contact information public"),
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        default=Decimal("0.00"),
    )
    rental_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        default=Decimal("0.00"),
        help_text=_("Price per hour for rental items"),
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
        choices=StatusType,
        default=StatusType.DRAFT,
    )
    workflow_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Temporal workflow ID for AI processing",
    )

    # Custom manager
    objects = ItemManager()

    # Add class constants for easy access
    CONDITION_CHOICES = ConditionType.choices
    ITEM_TYPE_CHOICES = ItemType.choices

    def __str__(self):
        return self.name or f"Item {self.pk}"

    @property
    def item_type(self) -> ItemType:
        """Determine item type based on prices."""
        if self.sale_price and not self.rental_price:
            return ItemType.FOR_SALE
        if self.rental_price:
            return ItemType.RENT
        return ItemType.BOTH

    def is_ready_for_display(self):
        """Check if item has minimum required fields to be displayed."""
        return bool(self.name and self.category)

    def get_first_image(self):
        """Return the first image of the item based on ordering."""
        return self.images.order_by("ordering").first()


def upload_to_item_images(instance: "Image", filename: str):
    extension: str = Path(filename).suffix or ".jpg"
    item_prefix: str = f"items/{str(instance.item.uuid)[0:4]}/{instance.item.uuid}"
    return f"{item_prefix}/{uuid.uuid4()}/original{extension}"


class Image(models.Model):
    original = models.ImageField(upload_to=upload_to_item_images, max_length=255)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    ordering = models.IntegerField(default=0)

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
        folder = f"temp/{suffix}/{str(self.item.uuid)[0:4]}/{self.pk}"
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
