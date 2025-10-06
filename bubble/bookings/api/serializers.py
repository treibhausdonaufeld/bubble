from rest_framework import serializers

from bubble.bookings.models import Booking
from bubble.items.models import Item


class BookingSerializer(serializers.ModelSerializer):
    """Detailed serializer for Booking where `item` is represented only by UUID."""

    item = serializers.SlugRelatedField(slug_field="uuid", queryset=Item.objects.all())

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "item",
            "user",
            "time_from",
            "time_to",
            "offer",
            "counter_offer",
            "accepted_by",
            "date_created",
            "date_updated",
        ]
        read_only_fields = ["id", "user", "date_created", "date_updated"]


class BookingListSerializer(serializers.ModelSerializer):
    item = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    class Meta:
        model = Booking
        fields = ["id", "status", "item", "user", "date_created"]
