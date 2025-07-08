import uuid
from decimal import Decimal
from pathlib import Path

from django.db import models
from django.utils.translation import gettext_lazy as _

from bubble.categories.models import ItemCategory
from config.settings.base import AUTH_USER_MODEL


class StatusType(models.IntegerChoices):
    NEW = 0, _("New")
    USED = 1, _("Used")
    OLD = 2, _("Old")


class ItemType(models.IntegerChoices):
    FOR_SALE = 0, _("For Sale")
    RENT = 1, _("Rent")


class ProcessingStatus(models.IntegerChoices):
    DRAFT = 0, _("Draft")
    PROCESSING = 1, _("Processing")
    COMPLETED = 2, _("Completed")
    FAILED = 3, _("Failed")


class Item(models.Model):
    active = models.BooleanField(default=True)
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.SET_NULL,
        related_name="items",
        blank=True,
        null=True,
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Unique identifier for the item"),
    )
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    intern = models.BooleanField(
        default=False,
        help_text=_("Internal item, not for public display"),
    )
    display_contact = models.BooleanField(
        default=False,
        help_text=_("Display contact information public"),
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        default=Decimal("0.00"),
    )
    th_payment = models.BooleanField(
        default=False,
        help_text=_("Payment via internal payment system"),
    )
    item_type = models.IntegerField(choices=ItemType, default=ItemType.FOR_SALE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    profile_img_frame = models.ImageField(upload_to="items/", blank=True, null=True)
    profile_img_frame_alt = models.CharField(max_length=255, blank=True)
    processing_status = models.IntegerField(
        choices=ProcessingStatus,
        default=ProcessingStatus.DRAFT,
    )

    # Store category-specific custom fields
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional fields specific to the item's category"),
    )

    # Add class constants for easy access
    STATUS_CHOICES = StatusType.choices
    ITEM_TYPE_CHOICES = ItemType.choices
    PROCESSING_STATUS_CHOICES = ProcessingStatus.choices
    STATUS_NEW = StatusType.NEW
    STATUS_USED = StatusType.USED
    STATUS_OLD = StatusType.OLD
    ITEM_TYPE_FOR_SALE = ItemType.FOR_SALE
    ITEM_TYPE_RENT = ItemType.RENT
    PROCESSING_DRAFT = ProcessingStatus.DRAFT
    PROCESSING_PROCESSING = ProcessingStatus.PROCESSING
    PROCESSING_COMPLETED = ProcessingStatus.COMPLETED
    PROCESSING_FAILED = ProcessingStatus.FAILED

    def __str__(self):
        return self.name or f"Item {self.pk}"

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
