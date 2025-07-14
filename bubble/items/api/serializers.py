"""Serializers for items API."""

from rest_framework import serializers

from bubble.items.models import Image, Item, ItemCategory


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for ItemCategory model"""

    class Meta:
        model = ItemCategory
        fields = ["id", "name", "description", "emoji", "parent_category", "ordering"]


class CategorySelect2Serializer(serializers.ModelSerializer):
    """Serializer for Select2 dropdown format"""

    text = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = ItemCategory
        fields = ["id", "text", "category_name"]

    def get_text(self, obj):
        """Build full hierarchy path for display"""
        hierarchy_path = []
        current = obj
        while current:
            hierarchy_path.insert(0, current.name)
            current = current.parent_category
        return " > ".join(hierarchy_path)


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer for category tree structure"""

    subcategories = serializers.SerializerMethodField()
    hierarchy_path = serializers.SerializerMethodField()

    class Meta:
        model = ItemCategory
        fields = [
            "id",
            "name",
            "description",
            "emoji",
            "parent_category",
            "ordering",
            "subcategories",
            "hierarchy_path",
        ]

    def get_subcategories(self, obj):
        """Get immediate subcategories"""
        subcategories = obj.subcategories.all().order_by("ordering", "name")
        return CategoryTreeSerializer(subcategories, many=True).data

    def get_hierarchy_path(self, obj):
        """Get the full hierarchy path"""
        hierarchy_path = []
        current = obj
        while current:
            hierarchy_path.insert(0, current.name)
            current = current.parent_category
        return " > ".join(hierarchy_path)


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
    category = serializers.SlugRelatedField(
        slug_field="name",
        queryset=ItemCategory.objects.all(),
        allow_null=True,
        required=False,
    )
    category_display = ItemCategorySerializer(source="category", read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = "__all__"
        read_only_fields = [
            "id",
            "user",
            "date_created",
            "date_updated",
            "images",
            "first_image",
            "category_display",
        ]

    def get_first_image(self, obj):
        """Get the first image of the item."""
        first_image = obj.get_first_image()
        if first_image:
            return ImageSerializer(first_image).data
        return None


class ItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for item lists."""

    category = serializers.SlugRelatedField(
        slug_field="name",
        queryset=ItemCategory.objects.all(),
        allow_null=True,
        required=False,
    )
    category_display = ItemCategorySerializer(source="category", read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = "__all__"
        read_only_fields = ["category_display"]

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
