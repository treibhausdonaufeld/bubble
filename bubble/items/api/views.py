"""API views for items."""

from django_filters.rest_framework import DjangoFilterBackend
from guardian.shortcuts import get_objects_for_user
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from bubble.items.ai.image_analyze import analyze_image
from bubble.items.api.serializers import (
    ImageSerializer,
    ItemListSerializer,
    ItemSerializer,
)
from bubble.items.models import Image, Item, StatusType

from .filters import ItemFilter


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for retrieving, creating, updating, and deleting items.
    """

    lookup_field = "uuid"
    queryset = Item.objects.all().select_related("user").prefetch_related("images")

    # Filtering / searching / ordering
    filterset_class = ItemFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # Search delegates to ItemFilter.search but DRF SearchFilter assists direct fields
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "updated_at", "sale_price", "rental_price"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ("list", "my_items", "published"):
            return ItemListSerializer
        return ItemSerializer

    def perform_create(self, serializer):
        """Set the user when creating an item."""
        serializer.save(user=self.request.user)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def published(self, request):
        queryset = self.get_queryset().filter(status__in=StatusType.published())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_items(self, request):
        """Get only the current user's items."""
        queryset = (
            Item.objects.filter(user=request.user)
            .select_related("user")
            .prefetch_related("images")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def reorder_images(self, request, uuid=None):
        """Reorder images for an item."""
        item = self.get_object()

        # Check if the user owns the item
        if item.user != request.user:
            return Response({"error": "Permission denied"}, status=403)

        image_order = request.data.get("image_order", [])

        if not isinstance(image_order, list):
            return Response({"error": "image_order must be a list"}, status=400)

        # Validate that all image UUIDs belong to this item
        item_image_uuids = {str(img.uuid) for img in item.images.all()}
        provided_image_uuids = {str(img_uuid) for img_uuid in image_order}

        if not provided_image_uuids.issubset(item_image_uuids):
            return Response({"error": "Invalid image UUIDs provided"}, status=400)

        # Update the ordering of each image
        for index, image_uuid in enumerate(image_order):
            Image.objects.filter(uuid=image_uuid, item=item).update(ordering=index)

        return Response({"success": True})

    @action(detail=True, methods=["put"])
    def ai_describe_item(self, request, uuid=None):
        """Ai describe the item and populate fields."""
        item = self.get_object()

        # Check if the user owns the item
        if item.user != request.user:
            return Response({"error": "Permission denied"}, status=403)

        analyze_response = analyze_image(item.get_first_image().uuid)

        item.name = analyze_response.title
        item.description = analyze_response.description
        item.category = analyze_response.category
        item.sale_price = analyze_response.price
        item.save()

        serializer = self.get_serializer(item)
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for retrieving images.
    Only authenticated users can access images.
    Users can only see images of items they have access to.
    """

    serializer_class = ImageSerializer
    lookup_field = "uuid"
    ordering = ["item", "ordering"]

    # we can use generic permissions here as the queryset limits strictly
    # to only editable items for the user
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        """Return images that the user can access."""
        user = self.request.user

        # Get all items where user has change_item permission
        items_with_change_permission = get_objects_for_user(
            user, "items.change_item", klass=Item, accept_global_perms=False
        )

        queryset = Image.objects.filter(
            item_id__in=items_with_change_permission.values_list("pk", flat=True)
        )

        # Filter by item if specified
        item_uuid = self.request.query_params.get("item")
        if item_uuid is not None:
            queryset = queryset.filter(item__uuid=item_uuid)

        return queryset

    def perform_create(self, serializer):
        """Set ordering automatically if not provided."""
        # If ordering is not provided, set it based on existing images count
        ordering = serializer.validated_data.get("ordering")
        if "ordering" not in serializer.validated_data or ordering is None:
            item = serializer.validated_data.get("item")
            if item:
                # Get the count of existing images for this item
                existing_count = Image.objects.filter(item=item).count()
                serializer.save(ordering=existing_count)
                return

        serializer.save()
