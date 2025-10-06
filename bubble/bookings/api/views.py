from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions

from bubble.bookings.api.filters import BookingFilter, MessageFilter
from bubble.bookings.api.serializers import (
    BookingListSerializer,
    BookingSerializer,
    MessageSerializer,
)
from bubble.bookings.models import Booking, BookingStatus, Message


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for bookings with filtering and permissions."""

    lookup_field = "uuid"
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_class = BookingFilter
    search_fields = ["item__name", "user__username"]
    ordering_fields = ["created_at", "updated_at", "status"]
    ordering = ["-updated_at"]
    permission_classes = [DjangoModelPermissions]

    def get_serializer_class(self):
        if self.action in ("list",):
            return BookingListSerializer
        return BookingSerializer

    def get_queryset(self):
        return Booking.objects.get_for_user(self.request.user).select_related(
            "item", "user", "accepted_by"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Make sure that the user can only set status to certain values"""
        if (
            self.request.user_id == serializer.instance.user_id
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
