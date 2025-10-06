from django_filters.rest_framework import DjangoFilterBackend
from guardian.shortcuts import get_objects_for_user
from items.models import Item
from rest_framework import filters, viewsets
from rest_framework.permissions import DjangoModelPermissions

from bubble.bookings.api.filters import BookingFilter
from bubble.bookings.api.serializers import BookingListSerializer, BookingSerializer
from bubble.bookings.models import Booking


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
    ordering_fields = ["date_created", "date_updated", "status"]
    ordering = ["-date_updated"]
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
