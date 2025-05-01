from django.db import models
from listings.models import Item
from bookings.models import Booking
from config.settings.base import AUTH_USER_MODEL


class InternPayment(models.Model):
  STATUS_CHOICES = ((1, 'Pending'), (2, 'Completed'), (3, 'Failed'),
                    (4, 'Refunded'))

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
