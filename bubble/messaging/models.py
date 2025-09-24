from django.db import models
from django.db.models import Q
from django.utils import timezone

from bubble.items.models import Item
from config.settings.base import AUTH_USER_MODEL


class Message(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )
    sender = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    receiver = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    date_created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date_created"]

    def __str__(self):
        if self.item:
            return (
                f"Message from {self.sender.username} to "
                f"{self.receiver.username} about {self.item.name}"
            )
        return f"Message from {self.sender.username} to {self.receiver.username}"

    @classmethod
    def get_conversation(cls, user1, user2, item=None):
        """Get all messages between two users, optionally filtered by item"""
        query = cls.objects.filter(
            sender__in=[user1, user2],
            receiver__in=[user1, user2],
        )
        if item is not None:
            query = query.filter(item=item)
        else:
            query = query.filter(item__isnull=True)
        return query.order_by("date_created")

    @classmethod
    def get_user_conversations(cls, user):
        """Get all unique conversations for a user grouped by other user and item"""
        # Get all messages where user is sender or receiver
        messages = cls.objects.filter(Q(sender=user) | Q(receiver=user)).select_related(
            "sender", "receiver", "item"
        )

        # Group by conversation (other_user + item combination)
        conversations = {}
        for msg in messages:
            other_user = msg.receiver if msg.sender == user else msg.sender
            key = (other_user.id, msg.item.id if msg.item else None)

            if key not in conversations:
                conversations[key] = {
                    "other_user": other_user,
                    "item": msg.item,
                    "last_message": msg,
                    "unread_count": 0,
                }
            # Update last message if this one is newer
            elif msg.date_created > conversations[key]["last_message"].date_created:
                conversations[key]["last_message"] = msg

            # Count unread messages
            if not msg.is_read and msg.receiver == user:
                conversations[key]["unread_count"] += 1

        return sorted(
            conversations.values(),
            key=lambda x: x["last_message"].date_created,
            reverse=True,
        )

    def mark_as_read(self):
        """Mark message as read with timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])
