"""Serializers for items API."""

from django.utils.translation import gettext_lazy as _
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers, status

from bubble.items.models import Image, Item, money_defaults


class ItemOwnerException(serializers.ValidationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("You can only create images for items you own.")
    default_code = "permission_denied"


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image model."""

    item = serializers.SlugRelatedField(slug_field="uuid", queryset=Item.objects.all())
    thumbnail = serializers.ImageField(read_only=True)
    preview = serializers.ImageField(read_only=True)
    ordering = serializers.IntegerField(required=False, allow_null=True)

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
        read_only_fields = ["uuid", "thumbnail", "preview"]

    def get_fields(self):
        """Override to make fields read-only on update."""
        fields = super().get_fields()

        # For existing instances (updates), only allow ordering to be modified
        if self.instance is not None:
            fields["original"].read_only = True
            fields["item"].read_only = True

        return fields

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
    user = serializers.SlugRelatedField(read_only=True, slug_field="uuid")
    first_image = serializers.SerializerMethodField()
    sale_price = MoneyField(**money_defaults, required=False, allow_null=True)
    rental_price = MoneyField(**money_defaults, required=False, allow_null=True)

    class Meta:
        model = Item
        exclude = ["id"]
        read_only_fields = [
            "uuid",
            "user",
            "created_at",
            "date_updated",
            "images",
        ]

    def get_first_image(self, obj):
        """Get the first image of the item."""
        first_image = obj.get_first_image()
        if first_image:
            request = self.context.get("request")
            if first_image.thumbnail and request:
                return request.build_absolute_uri(first_image.thumbnail.url)
            if first_image.thumbnail:
                return first_image.thumbnail.url
        return None

    def validate(self, attrs):
        """
        Ensure that both sale_price and rental_price are not set at the same time.

        This validator respects partial updates: if one of the fields is not
        provided in `attrs`, the existing instance value is considered.
        """
        sale = attrs.get("sale_price")
        rental = attrs.get("rental_price")

        # Both non-null is not allowed
        if sale is not None and rental is not None:
            raise serializers.ValidationError(
                {
                    "sale_price": _(
                        "Cannot set both sale_price and rental_price. Choose one."
                    ),
                    "rental_price": _(
                        "Cannot set both sale_price and rental_price. Choose one."
                    ),
                }
            )

        return super().validate(attrs)


class ItemListSerializer(ItemSerializer):
    """Lightweight serializer for item lists."""

    images = None


class ItemMinimalSerializer(ItemListSerializer):
    class Meta:
        model = Item
        fields = ["uuid", "name", "first_image"]
