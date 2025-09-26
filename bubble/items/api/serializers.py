"""Serializers for items API."""

from rest_framework import serializers

from bubble.items.models import Image, Item


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image model."""

    filename = serializers.ReadOnlyField()

    class Meta:
        model = Image
        fields = ["id", "original", "filename", "ordering"]
        read_only_fields = ["id"]


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""

    images = ImageSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = "__all__"
        read_only_fields = [
            "uuid",
            "user",
            "created_at",
            "date_updated",
            "images",
            "first_image",
        ]

    def get_first_image(self, obj):
        """Get the first image of the item."""
        first_image = obj.get_first_image()
        if first_image:
            return ImageSerializer(first_image).data
        return None


class ItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for item lists."""

    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = "__all__"

    def get_first_image(self, obj):
        """Get the first image of the item."""
        first_image = obj.get_first_image()
        if first_image:
            return {
                "uuid": first_image.uuid,
                "original": first_image.original.url if first_image.original else None,
                "filename": first_image.filename,
            }
        return None
