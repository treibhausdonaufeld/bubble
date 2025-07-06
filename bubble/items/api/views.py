"""API views for items."""

import mimetypes
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponse
from PIL import Image as PILImage
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bubble.items.api.serializers import (
    ImageSerializer,
    ItemListSerializer,
    ItemSerializer,
)
from bubble.items.models import Image, Item


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for retrieving, creating, updating, and deleting items.
    Only authenticated users can access items.
    Users can only see their own items and modify them.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == "list":
            return ItemListSerializer
        return ItemSerializer

    def get_queryset(self):
        """Return items that the user can access."""
        user = self.request.user

        queryset = (
            Item.objects.filter(user=user)
            .select_related("user", "category")
            .prefetch_related("images")
        )

        # Filter by item type if specified
        item_type = self.request.query_params.get("item_type")
        if item_type is not None:
            queryset = queryset.filter(item_type=item_type)

        # Filter by category if specified
        category = self.request.query_params.get("category")
        if category is not None:
            queryset = queryset.filter(category_id=category)

        # Filter by processing status if specified
        processing_status = self.request.query_params.get("processing_status")
        if processing_status is not None:
            queryset = queryset.filter(processing_status=processing_status)

        # Filter by active status (default to active only)
        active = self.request.query_params.get("active", "")
        if active.lower() == "true":
            queryset = queryset.filter(active=True)
        elif active.lower() == "false":
            queryset = queryset.filter(active=False)

        return queryset.order_by("-date_created")

    def perform_create(self, serializer):
        """Set the user when creating an item."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_items(self, request):
        """Get only the current user's items."""
        queryset = (
            Item.objects.filter(user=request.user)
            .select_related("user", "category")
            .prefetch_related("images")
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def public_items(self, request):
        """Get only public items (not intern)."""
        queryset = (
            Item.objects.filter(intern=False, active=True)
            .select_related("user", "category")
            .prefetch_related("images")
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving images.
    Only authenticated users can access images.
    Users can only see images of items they have access to.
    """

    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return images that the user can access."""
        user = self.request.user

        # Users can see images of their own items and public items
        queryset = (
            Image.objects.filter(Q(item__user=user) | Q(item__intern=False))
            .select_related("item")
            .order_by("item", "ordering")
        )

        # Filter by item if specified
        item_id = self.request.query_params.get("item")
        if item_id is not None:
            queryset = queryset.filter(item_id=item_id)

        return queryset

    # add endpoint to get binary representation of the original image
    @action(detail=True, methods=["get"], url_path="original")
    def get_original_image(self, request, pk=None):
        """Get the original image file."""

        try:
            image = self.get_object()
            if not image.original:
                return Response({"detail": "Original image not available."}, status=404)

            content_type, _ = mimetypes.guess_type(image.original.name)
            response = HttpResponse(
                image.original.read(),
                content_type=content_type or "application/octet-stream",
            )
            response["Content-Disposition"] = f'attachment; filename="{image.filename}"'
        except Image.DoesNotExist:
            return Response({"detail": "Image not found."}, status=404)
        else:
            return response

    @action(detail=True, methods=["get"], url_path="preview")
    def get_preview_image(self, request, pk=None):
        """Get a preview (scaled-down) version of the image."""
        image = self.get_object()
        if not image.original:
            return Response({"detail": "Original image not available."}, status=404)

        # Generate preview filename
        preview_name = image.get_preview_path()

        # Check if preview already exists
        if default_storage.exists(preview_name):
            # Serve existing preview
            with default_storage.open(preview_name, "rb") as preview_file:
                content_type, _ = mimetypes.guess_type(preview_name)
                response = HttpResponse(
                    preview_file.read(),
                    content_type=content_type or "image/jpeg",
                )
                response["Content-Disposition"] = (
                    f'inline; filename="{Path.name(preview_name)}"'
                )
                return response

        # Generate new preview
        with default_storage.open(image.original.name, "rb") as original_file:
            # Open image with PIL
            pil_image = PILImage.open(original_file)

            # Convert to RGB if necessary (for PNG with transparency)
            if pil_image.mode in ("RGBA", "P"):
                pil_image = pil_image.convert("RGB")

            # Calculate new dimensions (max 300px on longest side)
            max_size = 1600
            width, height = pil_image.size

            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)

            # Resize image
            pil_image = pil_image.resize(
                (new_width, new_height),
                PILImage.Resampling.LANCZOS,
            )

            # Save to BytesIO
            output = BytesIO()
            pil_image.save(output, format="JPEG", quality=85, optimize=True)
            output.seek(0)

            # Save preview to storage
            preview_file = ContentFile(output.getvalue())
            default_storage.save(preview_name, preview_file)

            # Return preview
            output.seek(0)
            response = HttpResponse(
                output.getvalue(),
                content_type="image/jpeg",
            )
            response["Content-Disposition"] = (
                f'inline; filename="{Path.name(preview_name)}"'
            )
            return response
