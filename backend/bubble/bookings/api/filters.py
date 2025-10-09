import django_filters

from bubble.bookings.models import Booking, BookingStatus, Message


class BookingFilter(django_filters.FilterSet):
    # Allow filtering by multiple statuses (e.g. ?status=1,2)
    status = django_filters.MultipleChoiceFilter(
        field_name="status", choices=BookingStatus.choices, conjoined=False
    )
    item = django_filters.UUIDFilter(field_name="item__uuid")
    user = django_filters.NumberFilter(field_name="user__id")
    created_at_after = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_before = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Booking
        fields = ["status", "item", "user", "created_at_after", "created_at_before"]


class MessageFilter(django_filters.FilterSet):
    booking = django_filters.UUIDFilter(field_name="booking__uuid")
    sender = django_filters.NumberFilter(field_name="sender__id")
    created_at_after = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_before = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    is_read = django_filters.BooleanFilter(field_name="is_read")

    class Meta:
        model = Message
        fields = ["booking", "sender", "created_at_after", "created_at_before"]
