import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from simple_history.models import HistoricalRecords

from bubble.items.models import Item, money_defaults
from config.settings.base import AUTH_USER_MODEL


class Booking(models.Model):
    STATUS_CHOICES = (
        (1, _("Pending")),
        (2, _("Confirmed")),
        (3, _("Cancelled")),
        (4, _("Completed")),
    )

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    time_from = models.DateTimeField(blank=True, null=True)
    time_to = models.DateTimeField(blank=True, null=True)

    offer = MoneyField(
        **money_defaults,
        blank=True,
        null=True,
        default_currency=settings.DEFAULT_CURRENCY,
        help_text=_("Offered price for the booking"),
    )
    counter_offer = MoneyField(
        **money_defaults,
        blank=True,
        null=True,
        default_currency=settings.DEFAULT_CURRENCY,
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

    def __str__(self):
        return f"Booking for {self.item.name} by {self.user}"


class Message(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
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
