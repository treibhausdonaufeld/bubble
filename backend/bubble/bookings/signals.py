import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _
from guardian.shortcuts import get_users_with_perms

from bubble.core.websocket_signals import send_message_notification

from .models import Booking, Message

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def notify_new_message(sender, instance: Message, created, **kwargs):
    """Notify item owners when a new message is created."""
    if not created:
        return

    # Get the item from the booking
    item = instance.booking.item

    # Get all users with change permission on this item
    users_with_perms = get_users_with_perms(
        item, only_with_perms_in=["change_item"], with_group_users=False
    )

    if instance.booking.user != instance.sender:
        send_message_notification(
            instance.booking.user_id,  # type: ignore[union-attr]
            message=instance.message,
            booking_uuid=str(instance.booking.uuid),
        )
        logger.info(
            "Sent new message notification to user %s for message %s",
            instance.booking.user.username,
            instance.uuid,
        )
    else:
        # Send notification to each user with change permission (except the sender)
        for user in users_with_perms:
            if user.id != instance.sender_id:  # type: ignore[union-attr]
                send_message_notification(
                    user.id,  # type: ignore[union-attr]
                    message=instance.message,
                    booking_uuid=str(instance.booking.uuid),
                )
                logger.info(
                    "Sent new message notification to user %s for message %s",
                    getattr(user, "username", str(user)),
                    instance.uuid,
                )


@receiver(post_save, sender=Booking)
def notify_new_booking(sender, instance: Booking, created, **kwargs):
    """Notify item owners when a new booking is created."""
    if not created:
        return

    # Get the item
    item = instance.item

    # Get all users with change permission on this item
    users_with_perms = get_users_with_perms(
        item, only_with_perms_in=["change_item"], with_group_users=False
    )

    # Send notification to each user with change permission (except the booking creator)
    for user in users_with_perms:
        if user.id != instance.user_id:  # type: ignore[union-attr]
            send_message_notification(
                user.id,  # type: ignore[union-attr]
                message=_("A new booking has been created for your item."),
            )
            logger.info(
                "Sent new booking notification to user %s for booking %s",
                getattr(user, "username", str(user)),
                instance.uuid,
            )
