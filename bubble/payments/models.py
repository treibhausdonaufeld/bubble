from django.db import models
from django.utils.translation import gettext_lazy as _
from bubble.items.models import Item
from bubble.bookings.models import Booking
from config.settings.base import AUTH_USER_MODEL


class InternPayment(models.Model):
  STATUS_CHOICES = ((1, _('Pending')), (2, _('Completed')), (3, _('Failed')),
                    (4, _('Refunded')))

  booking = models.ForeignKey(Booking,
                              on_delete=models.CASCADE,
                              related_name='payments',
                              blank=True,
                              null=True)
  item = models.ForeignKey(Item,
                           on_delete=models.CASCADE,
                           related_name='payments',
                           blank=True,
                           null=True)
  user = models.ForeignKey(AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='payments')
  date_created = models.DateTimeField(auto_now_add=True)
  status = models.IntegerField(choices=STATUS_CHOICES, default=1)

  def __str__(self):
    if self.booking:
      return f"Payment for booking {self.booking.id} by {self.user.username}"
    return f"Payment for {self.item.name} by {self.user.username}"
