"""Serializers for items API."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status

from bubble.items.models import Image, Item


class ItemOwnerException(serializers.ValidationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("You can only create images for items you own.")
    default_code = "permission_denied"


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image model."""

    item = serializers.SlugRelatedField(slug_field="uuid", queryset=Item.objects.all())
    thumbnail = serializers.ImageField(read_only=True)
    preview = serializers.ImageField(read_only=True)

    class Meta:
        model = Image
        fields = [
            "uuid",
            "original",
            "ordering",
            "thumbnail",
            "preview",
            "item",
        ]
        read_only_fields = ["id"]

    def validate_item(self, value):
        """Ensure only item owners can create images for their items."""
        request = self.context.get("request")
        if request and request.user:
            if value.user != request.user:
                raise ItemOwnerException
        return value


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
