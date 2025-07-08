from rest_framework import serializers

from bubble.categories.models import ItemCategory


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
