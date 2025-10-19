from __future__ import annotations

import logging

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from bubble.bookings.models import Booking, BookingStatus
from bubble.items.models import Item, ItemStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def check_bookings_active(self) -> None:
    """Periodic task: ensure items reflect active/ended bookings.

    Runs every 10 minutes. For confirmed bookings that are currently active
    (time_from <= now <= time_to or time_to is null), set the linked item
    to ItemStatus.RENTED if it is currently AVAILABLE.

    For bookings that were confirmed but are no longer active (time_to < now),
    if the linked item has no other active confirmed bookings, set it back to
    ItemStatus.AVAILABLE (only if currently RENTED).
    """
    now = timezone.now()
    logger.debug("Running check_bookings_active task at %s", now)

    # Query for active confirmed bookings
    active_q = (
        Q(status=BookingStatus.CONFIRMED)
        & Q(time_from__lte=now)
        & (Q(time_to__isnull=True) | Q(time_to__gte=now))
    )

    active_item_ids_qs = Booking.objects.filter(active_q).values_list(
        "item_id", flat=True
    )
    # Set items that are AVAILABLE -> RENTED
    updated = Item.objects.filter(
        id__in=active_item_ids_qs,
        status__in=[ItemStatus.AVAILABLE, ItemStatus.RESERVED],
    ).update(status=ItemStatus.RENTED)
    if updated:
        logger.info("Marked %d items as RENTED (active bookings)", updated)

    # Now handle bookings that ended (confirmed bookings with time_to < now)
    ended_q = Q(status=BookingStatus.CONFIRMED) & Q(time_to__lt=now)
    ended_item_ids_qs = Booking.objects.filter(ended_q).values_list(
        "item_id", flat=True
    )

    freed = Item.objects.filter(
        id__in=ended_item_ids_qs,
        status=ItemStatus.RENTED,
    ).update(status=ItemStatus.AVAILABLE)
    if freed:
        logger.info("Marked %d items as AVAILABLE (no more active bookings)", freed)
