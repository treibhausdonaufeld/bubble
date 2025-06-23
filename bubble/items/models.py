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
    GIVE_AWAY = 1, _("Give Away")
    BORROW = 2, _("Borrow")
    NEED = 3, _("Need")


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
    display_contact = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    th_payment = models.BooleanField(default=False, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.IntegerField(blank=True, null=True, choices=StatusType)
    item_type = models.IntegerField(choices=ItemType, default=ItemType.FOR_SALE)
    profile_img_frame = models.ImageField(upload_to="items/", blank=True, null=True)
    profile_img_frame_alt = models.CharField(max_length=255, blank=True)

    # Add class constants for easy access
    STATUS_CHOICES = StatusType.choices
    ITEM_TYPE_CHOICES = ItemType.choices
    STATUS_NEW = StatusType.NEW
    STATUS_USED = StatusType.USED
    STATUS_OLD = StatusType.OLD
    ITEM_TYPE_FOR_SALE = ItemType.FOR_SALE
    ITEM_TYPE_GIVE_AWAY = ItemType.GIVE_AWAY
    ITEM_TYPE_BORROW = ItemType.BORROW
    ITEM_TYPE_NEED = ItemType.NEED

    def __str__(self):
        return self.name


class Image(models.Model):
    fname = models.ImageField(upload_to="items/images/")
    fname_alt = models.CharField(max_length=255, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    ordering = models.IntegerField(default=0)

    def __str__(self):
        return f"Image for {self.item.name} ({self.fname})"
