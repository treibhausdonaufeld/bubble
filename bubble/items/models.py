import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from guardian.shortcuts import assign_perm
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToCover, ResizeToFill
from simple_history.models import HistoricalRecords

from config.settings.base import AUTH_USER_MODEL

money_defaults = {
    "max_digits": 10,
    "decimal_places": 2,
}


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

    @classmethod
    def published(cls):
        return (cls.AVAILABLE, cls.RESERVED, cls.RENTED, cls.SOLD)


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
        if not user.is_authenticated:
            return self.none()
        return self.filter(user=user)


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

    # enable history tracking
    history = HistoricalRecords()

    # Custom manager
    objects = ItemManager()

    # Add class constants for easy access
    CONDITION_CHOICES = ConditionType.choices
    ITEM_TYPE_CHOICES = ItemType.choices

    class Meta:
        ordering = ["-created_at"]

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
            # give all object permission to self.request.user on instance
            assign_perm("change_item", self.user, obj=self)
            assign_perm("delete_item", self.user, obj=self)

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


class ItemUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Item, on_delete=models.CASCADE)


class ItemGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Item, on_delete=models.CASCADE)


def upload_to_item_images(instance: "Image", filename: str):
    extension: str = Path(filename).suffix or ".jpg"
    item_prefix: str = f"items/{str(instance.item.uuid)[0:4]}/{instance.item.uuid}"
    return f"{item_prefix}/{uuid.uuid4()}/original{extension}"


class Image(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
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
