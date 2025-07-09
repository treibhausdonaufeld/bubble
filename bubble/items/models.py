from django.db import models
from django.utils.translation import gettext_lazy as _

from bubble.categories.models import ItemCategory
from config.settings.base import AUTH_USER_MODEL


class StatusType(models.IntegerChoices):
    NEW = 0, _("New")
    USED = 1, _("Used")
    OLD = 2, _("Old")


class Item(models.Model):
    active = models.BooleanField(default=True)
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    intern = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Store category-specific custom fields
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional fields specific to the item's category"),
    )

    def __str__(self):
        return self.name

    def get_first_image(self):
        """Return the first image of the item based on ordering."""
        return self.images.order_by("ordering").first()


def upload_to_item_images(instance, filename):
    return f"items/original/{instance.item.pk}/{filename}"


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
