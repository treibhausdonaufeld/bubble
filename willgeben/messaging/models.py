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
  is_read = models.BooleanField(default=False)

  class Meta:
    ordering = ['date_created']

  def __str__(self):
    return f"Message from {self.sender.username} to {self.receiver.username} about {self.item.name}"

  @classmethod
  def get_conversation(cls, item, user1, user2):
    """Get all messages between two users about a specific item"""
    return cls.objects.filter(
      item=item,
      sender__in=[user1, user2],
      receiver__in=[user1, user2]
    ).order_by('date_created')
