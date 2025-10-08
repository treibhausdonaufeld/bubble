from rest_framework import serializers

from bubble.bookings.models import Booking, Message
from bubble.items.api.serializers import ItemMinimalSerializer
from bubble.items.models import Item
from bubble.users.api.serializers import UserSerializer


class BookingSerializer(serializers.ModelSerializer):
    """Detailed serializer for Booking where `item` is represented only by UUID."""

    item = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Item.objects.published()
    )
    item_details = ItemMinimalSerializer(read_only=True, source="item")
    user = UserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "uuid",
            "status",
            "item",
            "item_details",
            "user",
            "time_from",
            "time_to",
            "offer",
            "counter_offer",
            "accepted_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "user", "created_at", "updated_at"]

    def validate(self, attrs):
        """
        Validate that if time_to is not set, the item must allow open-ended rentals.
        """
        time_to = attrs.get("time_to")
        item = attrs.get("item")

        # If time_to is not provided and we're creating/updating
        if time_to is None and item and not item.rental_open_end:
            raise serializers.ValidationError(
                {
                    "time_to": (
                        "End time is required for this item. "
                        "The item does not allow open-ended rentals."
                    )
                }
            )

        return super().validate(attrs)


class BookingListSerializer(BookingSerializer):
    item = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    class Meta:
        model = Booking
        fields = [
            "uuid",
            "status",
            "item",
            "item_details",
            "user",
            "created_at",
            "time_from",
            "time_to",
        ]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model. Booking is referenced by UUID."""

    booking = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Booking.objects.all()
    )
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = [
            "uuid",
            "booking",
            "sender",
            "created_at",
            "message",
        ]
        read_only_fields = ["uuid", "sender", "created_at"]
