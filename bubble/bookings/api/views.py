from django_filters.rest_framework import DjangoFilterBackend
from guardian.shortcuts import get_objects_for_user
from rest_framework import filters, viewsets
from rest_framework.permissions import DjangoModelPermissions

from bubble.bookings.api.filters import BookingFilter, MessageFilter
from bubble.bookings.api.serializers import (
    BookingListSerializer,
    BookingSerializer,
    MessageSerializer,
)
from bubble.bookings.models import Booking, Message
from bubble.items.models import Item


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for bookings with filtering and permissions."""

    lookup_field = "uuid"
    queryset = Booking.objects.select_related("item", "user", "accepted_by").all()
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
        user = self.request.user

        items_with_change_permission = get_objects_for_user(
            self.request.user,
            "items.change_item",
            klass=Item,
            accept_global_perms=False,
        )

        return self.queryset.filter(user=user) | self.queryset.filter(
            item__in=items_with_change_permission
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
