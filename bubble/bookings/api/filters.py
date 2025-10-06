import django_filters

from bubble.bookings.models import Booking


class BookingFilter(django_filters.FilterSet):
    # Allow filtering by multiple statuses (e.g. ?status=1,2)
    status = django_filters.MultipleChoiceFilter(
        field_name="status", choices=Booking.STATUS_CHOICES, conjoined=False
    )
    item = django_filters.UUIDFilter(field_name="item__uuid")
    user = django_filters.NumberFilter(field_name="user__id")
    date_created_after = django_filters.IsoDateTimeFilter(
        field_name="date_created", lookup_expr="gte"
    )
    date_created_before = django_filters.IsoDateTimeFilter(
        field_name="date_created", lookup_expr="lte"
    )

    class Meta:
        model = Booking
        fields = ["status", "item", "user", "date_created_after", "date_created_before"]
