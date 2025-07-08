from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bubble.categories.models import ItemCategory

from .serializers import (
    CategorySelect2Serializer,
    CategorySerializer,
    CategoryTreeSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for category operations.
    Provides list, retrieve, and custom actions for categories.
    """

    queryset = ItemCategory.objects.all().order_by("ordering", "name")
    serializer_class = CategorySerializer

    @action(detail=False, methods=["get"], url_path="select2")
    def select2(self, request):
        """
        Endpoint for Select2 dropdown with AJAX search support.
        Returns categories in Select2 format with full hierarchy paths.

        Query parameters:
        - q: search term (optional)
        - page: page number for pagination (optional)
        """
        search_term = request.query_params.get("q", "").strip()

        # Get all leaf categories (categories without subcategories)
        queryset = ItemCategory.objects.filter(
            parent_category__isnull=False,  # Has a parent
            subcategories__isnull=True,  # Has no children
        ).order_by("name")

        # Filter by search term if provided
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term)
                | Q(parent_category__name__icontains=search_term),
            )

        # Limit results to prevent too many options
        queryset = queryset[:50]

        # Serialize data
        serializer = CategorySelect2Serializer(queryset, many=True)

        return Response({"results": serializer.data, "pagination": {"more": False}})

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        """
        Get category tree structure starting from root categories.
        Returns nested category hierarchy.
        """
        # Get root categories
        root_categories = ItemCategory.objects.filter(
            parent_category__isnull=True,
        ).order_by("ordering", "name")

        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="subcategories")
    def subcategories(self, request, pk=None):
        """
        Get subcategories for a specific category.
        """
        category = self.get_object()
        subcategories = category.subcategories.all().order_by("ordering", "name")
        serializer = CategorySerializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="leaves")
    def leaves(self, request):
        """
        Get all leaf categories (categories without children).
        Useful for item categorization.
        """
        leaf_categories = ItemCategory.objects.filter(
            subcategories__isnull=True,
        ).order_by("name")

        search_term = request.query_params.get("search", "").strip()
        if search_term:
            leaf_categories = leaf_categories.filter(
                Q(name__icontains=search_term)
                | Q(parent_category__name__icontains=search_term),
            )

        serializer = CategoryTreeSerializer(leaf_categories, many=True)
        return Response(serializer.data)
