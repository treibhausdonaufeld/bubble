from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.items.models import Item


class Message(models.Model):
  item = models.ForeignKey(Item,
                           on_delete=models.CASCADE,
                           related_name='messages')
  sender = models.ForeignKey(AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='sent_messages')
  receiver = models.ForeignKey(AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='received_messages')
  date_created = models.DateTimeField(auto_now_add=True)
  message = models.TextField()

  def __str__(self):
    return f"Message from {self.sender.username} to {self.receiver.username} about {self.item.name}"
