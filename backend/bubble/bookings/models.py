import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from guardian.shortcuts import get_objects_for_user
from simple_history.models import HistoricalRecords

from bubble.items.models import Item, money_defaults
from config.settings.base import AUTH_USER_MODEL


class BookingStatus(models.IntegerChoices):
    PENDING = 1, _("Pending")
    CANCELLED = 2, _("Cancelled")
    CONFIRMED = 3, _("Confirmed")
    COMPLETED = 4, _("Completed")
    REJECTED = 5, _("Rejected")


class BookingManager(models.Manager):
    def get_for_user(self, user):
        items_with_change_permission = get_objects_for_user(
            user,
            "items.change_item",
            klass=Item,
            accept_global_perms=False,
        )

        return self.filter(user=user) | self.filter(
            item__in=items_with_change_permission
        )


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    status = models.IntegerField(
        choices=BookingStatus, default=BookingStatus.PENDING, verbose_name=_("Status")
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    time_from = models.DateTimeField(
        blank=True, null=True, default=timezone.now, verbose_name=_("Time From")
    )
    time_to = models.DateTimeField(blank=True, null=True, verbose_name=_("Time To"))

    offer = MoneyField(
        **money_defaults,
        blank=True,
        null=True,
        default_currency=settings.DEFAULT_CURRENCY,
        verbose_name=_("Offer"),
        help_text=_("Offered price for the booking"),
    )
    counter_offer = MoneyField(
        **money_defaults,
        blank=True,
        null=True,
        default_currency=settings.DEFAULT_CURRENCY,
        verbose_name=_("Counter Offer"),
        help_text=_("Counter offer price for the booking"),
    )

    accepted_by = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="accepted_bookings",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    objects = BookingManager()

    def __str__(self):
        return f"Booking for {self.item.name} by {self.user}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.sender}"
