from django.db import models
from django.utils.translation import gettext_lazy as _

from bubble.items.models import Item
from config.settings.base import AUTH_USER_MODEL


class Booking(models.Model):
    STATUS_CHOICES = (
        (1, _("Pending")),
        (2, _("Confirmed")),
        (3, _("Cancelled")),
        (4, _("Completed")),
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    date_from = models.DateField()
    date_to = models.DateField()
    time_from = models.TimeField(blank=True, null=True)
    time_to = models.TimeField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking for {self.item.name} by {self.user.username}"


class OpeningHour(models.Model):
    DAYS_OF_WEEK = (
        (1, _("Monday")),
        (2, _("Tuesday")),
        (3, _("Wednesday")),
        (4, _("Thursday")),
        (5, _("Friday")),
        (6, _("Saturday")),
        (7, _("Sunday")),
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="opening_hours",
    )
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    time_from = models.TimeField()
    time_to = models.TimeField()

    def __str__(self):
        return (
            f"{self.get_day_display()} {self.time_from} - "
            f"{self.time_to} for {self.item.name}"
        )


class ExceptionalOpeningHour(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="exceptional_hours",
    )
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()

    def __str__(self):
        return (
            f"Exception on {self.date}: {self.time_from} - "
            f"{self.time_to} for {self.item.name}"
        )
