from rest_framework import serializers
from users.api.serializers import UserSerializer

from bubble.bookings.models import Booking, Message
from bubble.items.api.serializers import ItemMinimalSerializer
from bubble.items.models import Item


class BookingSerializer(serializers.ModelSerializer):
    """Detailed serializer for Booking where `item` is represented only by UUID."""

    item = serializers.SlugRelatedField(slug_field="uuid", queryset=Item.objects.all())
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


class BookingListSerializer(serializers.ModelSerializer):
    item = serializers.SlugRelatedField(read_only=True, slug_field="uuid")
    item_details = ItemMinimalSerializer(read_only=True, source="item")

    class Meta:
        model = Booking
        fields = ["uuid", "status", "item", "user", "created_at"]


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
