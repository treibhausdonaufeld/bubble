"""Serializers for items API."""

from rest_framework import serializers

from bubble.categories.models import ItemCategory
from bubble.items.models import Image, Item


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image model."""

    filename = serializers.ReadOnlyField()

    class Meta:
        model = Image
        fields = ["id", "original", "filename", "ordering"]
        read_only_fields = ["id"]


class ItemCategorySerializer(serializers.ModelSerializer):
    """Serializer for ItemCategory model."""

    class Meta:
        model = ItemCategory
        fields = ["id", "name", "description"]
        read_only_fields = ["id", "name", "description"]


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""

    images = ImageSerializer(many=True, read_only=True)
    category = ItemCategorySerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ["__all__"]
        read_only_fields = [
            "id",
            "user",
            "date_created",
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

    category = ItemCategorySerializer(read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ["__all__"]
        read_only_fields = fields

    def get_first_image(self, obj):
        """Get the first image of the item."""
        first_image = obj.get_first_image()
        if first_image:
            return {
                "id": first_image.id,
                "original": first_image.original.url if first_image.original else None,
                "filename": first_image.filename,
            }
        return None
