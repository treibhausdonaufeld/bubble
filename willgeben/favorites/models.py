from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.items.models import Item


class Favorite(models.Model):
  user = models.ForeignKey(AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='favorites')
  item = models.ForeignKey(Item,
                           on_delete=models.CASCADE,
                           related_name='favorited_by')

  class Meta:
    unique_together = ('user', 'item')

  def __str__(self):
    return f"{self.user.username} favorites {self.item.name}"

# reservation of item on willgeben, but not time slot like booking, but "I want to reserve this item"
class Interest(models.Model):
  user = models.ForeignKey(AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='interests')
  item = models.ForeignKey(Item,
                           on_delete=models.CASCADE,
                           related_name='interested_by')
  comment = models.TextField(blank=True, null=True)
  date_created = models.DateTimeField(auto_now_add=True)

  class Meta:
    unique_together = ('user', 'item')

  def __str__(self):
    return f"{self.user.username} interested in {self.item.name}"
