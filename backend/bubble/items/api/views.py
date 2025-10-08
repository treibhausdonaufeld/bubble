"""API views for items."""

import contextlib
import uuid as _uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from bubble.items.ai.image_analyze import analyze_image
from bubble.items.ai.image_create import generate_image_from_prompt
from bubble.items.api.serializers import (
    ImageSerializer,
    ItemListSerializer,
    ItemSerializer,
)
from bubble.items.models import Image, Item

from .filters import ItemFilter


class ItemBaseViewSet(viewsets.GenericViewSet):
    """Base viewset with common settings for items."""

    lookup_field = "uuid"
    serializer_class = ItemListSerializer

    # Filtering / searching / ordering
    filterset_class = ItemFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "updated_at", "sale_price", "rental_price"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ("list", "my_items"):
            return ItemListSerializer
        return ItemSerializer


class PublicItemViewSet(viewsets.ReadOnlyModelViewSet, ItemBaseViewSet):
    """
    ViewSet for retrieving published items.
    This viewset is read-only and only returns items with a published status.
    """

    queryset = (
        Item.objects.published().select_related("user").prefetch_related("images")
    )
    permission_classes = [IsAuthenticatedOrReadOnly]


class ItemViewSet(viewsets.ModelViewSet, ItemBaseViewSet):
    """
    ViewSet for retrieving, creating, updating, and deleting items.
    """

    def get_queryset(self):
        """Return items belonging to the authenticated user."""
        return (
            Item.objects.get_for_user(self.request.user)
            .select_related("user")
            .prefetch_related("images")
        )

    def perform_create(self, serializer):
        """Set the user when creating an item."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["put"])
    def reorder_images(self, request, uuid=None):
        """Reorder images for an item."""
        item = self.get_object()

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
    def ai_describe(self, request, uuid=None):
        """Ai describe the item and populate fields."""
        item = self.get_object()

        first_image = item.get_first_image()
        if not first_image:
            raise ValidationError(_("Item has no images to analyze."))

        analyze_response = analyze_image(first_image.uuid)

        item.name = analyze_response.title
        item.description = analyze_response.description
        item.category = analyze_response.category
        with contextlib.suppress(DjangoValidationError):
            item.sale_price = analyze_response.price
            if item.sale_price is not None:
                item.rental_price = None  # Ensure only one price type is set
        item.save()

        serializer = self.get_serializer(item)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def ai_image(self, request, uuid=None):
        """Generate an image from the item's name and description and attach it.

        The generated image is created by a small Google image model and saved
        as a new Image.original file for the item. Returns the created image
        data via ImageSerializer.
        """
        item = self.get_object()

        # Build prompt from name and description
        text_parts = []
        if item.name:
            text_parts.append(item.name)
        if item.description:
            text_parts.append(item.description)

        if not text_parts:
            return Response({"detail": "Item has no name or description."}, status=400)

        prompt = "\n\n".join(text_parts)

        image_bytes, _mime = generate_image_from_prompt(prompt)

        # Save the generated image as an Image instance
        filename = f"generated-{_uuid.uuid4().hex[:8]}.png"
        content = ContentFile(image_bytes, name=filename)
        Image.objects.create(item=item, original=content)

        serializer = self.get_serializer(item, context={"request": request})
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
        queryset = Image.objects.filter(
            item_id__in=Item.objects.get_for_user(self.request.user).values_list(
                "pk", flat=True
            )
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
