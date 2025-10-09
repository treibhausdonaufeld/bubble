from django.db.models import Count, Q
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticatedOrReadOnly

from bubble.bookings.api.filters import BookingFilter, MessageFilter
from bubble.bookings.api.serializers import (
    BookingListSerializer,
    BookingSerializer,
    MessageSerializer,
)
from bubble.bookings.models import Booking, BookingStatus, Message


class PublicBookingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only ViewSet for confirmed bookings.

    This viewset only returns bookings with CONFIRMED status and is read-only.
    Supports filtering via BookingFilter.
    """

    lookup_field = "uuid"
    serializer_class = BookingSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_class = BookingFilter
    search_fields = ["item__name", "user__username"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("list",):
            return BookingListSerializer
        return BookingSerializer

    def get_queryset(self):
        """Return only confirmed bookings."""
        return Booking.objects.filter(status=BookingStatus.CONFIRMED).select_related(
            "item", "user", "accepted_by"
        )


class BookingViewSet(viewsets.ModelViewSet, PublicBookingViewSet):
    """ViewSet for bookings with filtering and permissions."""

    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        return (
            Booking.objects.get_for_user(self.request.user)
            .select_related("item", "user", "accepted_by")
            .annotate(
                unread_messages_count=Count(
                    "messages", filter=Q(messages__is_read=False)
                )
            )
        )

    def perform_create(self, serializer):
        """
        Create a booking and auto-confirm if the item has rental_self_service enabled.
        """
        item = serializer.validated_data.get("item")

        # Auto-confirm booking if item allows self-service rentals
        if item and item.rental_self_service:
            serializer.save(user=self.request.user, status=BookingStatus.CONFIRMED)
        else:
            serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Make sure that the user can only set status to certain values"""
        if (
            self.request.user == serializer.instance.user
            and serializer.validated_data.get("status")
            not in (BookingStatus.CANCELLED, BookingStatus.PENDING)
        ):
            msg = _("Invalid status change.")
            raise ValidationError(msg)

        serializer.save()


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for messages related to bookings.

    List requires either `booking` (booking-uuid) or `user` (user id) query param
    to be provided to avoid returning global message lists.
    """

    lookup_field = "uuid"
    queryset = Message.objects.select_related("booking", "sender").all()
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MessageFilter
    ordering_fields = ["created_at", "sender"]
    ordering = ["-created_at"]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        bookings_for_user = Booking.objects.get_for_user(self.request.user)
        return self.queryset.filter(booking__in=bookings_for_user)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
