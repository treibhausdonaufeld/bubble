import uuid
from decimal import Decimal
from pathlib import Path

from django.db import models
from django.utils.translation import gettext_lazy as _

from config.settings.base import AUTH_USER_MODEL


class ItemCategoryManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class ItemCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    parent_category = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        blank=True,
        null=True,
    )

    # Ordering field for menu display
    ordering = models.IntegerField(
        default=1,
        help_text=_("Order of display in navigation menu (lower numbers appear first)"),
    )

    objects = ItemCategoryManager()

    class Meta:
        verbose_name_plural = _("Item Categories")
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def get_hierarchy(self):
        """Returns the full category hierarchy path"""
        if self.parent_category:
            return f"{self.parent_category.get_hierarchy()} > {self.name}"
        return self.name

    @property
    def is_root_category(self):
        """Check if this is a root category (no parent)"""
        return self.parent_category is None

    def get_root_category(self):
        """Get the root category of this category's hierarchy"""
        if self.is_root_category:
            return self
        current = self
        while current.parent_category is not None:
            current = current.parent_category
        return current

    def is_leaf_category(self):
        """Check if this category has no subcategories (is a leaf category)"""
        return not self.subcategories.exists()

    def get_descendants(self, *, include_self=False):
        """Get all descendant categories"""
        descendants = []
        if include_self:
            descendants.append(self)

        # Recursively get all subcategories
        def _get_subcategories(category):
            for subcategory in category.subcategories.all():
                descendants.append(subcategory)
                _get_subcategories(subcategory)

        _get_subcategories(self)
        return descendants


class StatusType(models.IntegerChoices):
    NEW = 0, _("New")
    USED = 1, _("Used")
    BROKEN = 2, _("Broken")


class ItemType(models.IntegerChoices):
    FOR_SALE = 0, _("For Sale")
    RENT = 1, _("Rent")


class ProcessingStatus(models.IntegerChoices):
    DRAFT = 0, _("Draft")
    PROCESSING = 1, _("Processing")
    COMPLETED = 2, _("Completed")
    FAILED = 3, _("Failed")


class ItemManager(models.Manager):
    def for_user(self, user) -> models.QuerySet:
        """Return a queryset filtered by user permissions."""
        q = models.Q(active=True, internal=False)
        if user.is_authenticated:
            # allow also own items of this user
            q |= models.Q(user=user)
            if hasattr(user, "profile") and user.profile.internal:
                # allow all active items for internal users
                q |= models.Q(active=True)
        return self.filter(q)


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
    internal = models.BooleanField(
        default=False,
        help_text=_("Internal item, not for public display"),
    )
    display_contact = models.BooleanField(
        default=False,
        help_text=_("Display your contact information public"),
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        default=Decimal("0.00"),
    )
    payment_enabled = models.BooleanField(
        default=False,
        help_text=_("Enable payment via internal payment system"),
    )
    item_type = models.IntegerField(choices=ItemType, default=ItemType.FOR_SALE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.IntegerField(
        choices=StatusType,
        default=StatusType.USED,
        help_text=_("Condition of the item"),
    )
    processing_status = models.IntegerField(
        choices=ProcessingStatus,
        default=ProcessingStatus.DRAFT,
    )
    workflow_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Temporal workflow ID for AI processing",
    )

    # Custom manager
    objects = ItemManager()

    # Add class constants for easy access
    STATUS_CHOICES = StatusType.choices
    ITEM_TYPE_CHOICES = ItemType.choices
    PROCESSING_STATUS_CHOICES = ProcessingStatus.choices
    STATUS_NEW = StatusType.NEW
    STATUS_USED = StatusType.USED
    STATUS_BROKEN = StatusType.BROKEN
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
