"""API views for items."""

import mimetypes
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from PIL import Image as PILImage
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bubble.items.ai.image_analyze import analyze_image
from bubble.items.api.serializers import (
    ImageSerializer,
    ItemListSerializer,
    ItemSerializer,
)
from bubble.items.models import Image, Item


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for retrieving, creating, updating, and deleting items.
    """

    lookup_field = "uuid"

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ("list", "my_items"):
            return ItemListSerializer
        return ItemSerializer

    def get_queryset(self):
        """Return items that the user can access and that he owns."""
        user = self.request.user

        queryset = (
            Item.objects.available(user)
            .select_related("user")
            .prefetch_related("images")
        )

        # Filter by item type if specified
        item_type = self.request.query_params.get("item_type")
        if item_type is not None:
            queryset = queryset.filter(item_type=item_type)

        # Filter by category if specified
        category = self.request.query_params.get("category")
        if category is not None:
            queryset = queryset.filter(category=category)

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

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        """Set the user when creating an item."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_items(self, request):
        """Get only the current user's items."""
        queryset = (
            Item.objects.filter(user=request.user)
            .select_related("user")
            .prefetch_related("images")
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
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

    @action(detail=True, methods=["post"])
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

    def get_queryset(self):
        """Return images that the user can access."""
        user = self.request.user

        # Users can see images of their own items and public items
        queryset = (
            Image.objects.filter(item__in=Item.objects.for_user(user))
            .select_related("item")
            .order_by("item", "ordering")
        )

        # Filter by item if specified
        item_uuid = self.request.query_params.get("item")
        if item_uuid is not None:
            queryset = queryset.filter(item__uuid=item_uuid)

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

    def _generate_resized_image(self, image, max_size, quality=85, suffix="preview"):
        """
        Generate a resized version of an image.

        Args:
            image: Image model instance
            max_size: Maximum size for the longest side
            quality: JPEG quality (1-100)
            suffix: Suffix for the filename (e.g., 'preview', 'thumbnail')

        Returns:
            HttpResponse with the resized image
        """
        if not image.original:
            return Response({"detail": "Original image not available."}, status=404)

        # Get storage path from model method
        if suffix == "preview":
            resized_path = image.get_preview_path()
        elif suffix == "thumbnail":
            resized_path = image.get_thumbnail_path()
        else:
            return Response({"detail": "Invalid suffix."}, status=400)

        if not resized_path:
            return Response({"detail": "Unable to generate storage path."}, status=500)

        # Check if resized version already exists
        if default_storage.exists(resized_path):
            # Serve existing resized image
            with default_storage.open(resized_path, "rb") as resized_file:
                content_type, _ = mimetypes.guess_type(resized_path)
                response = HttpResponse(
                    resized_file.read(),
                    content_type=content_type or "image/jpeg",
                )
                response["Content-Disposition"] = (
                    f'inline; filename="{Path(resized_path).name}"'
                )
                return response

        # Generate new resized image
        with default_storage.open(image.original.name, "rb") as original_file:
            # Open image with PIL
            pil_image = PILImage.open(original_file)

            # Convert to RGB if necessary (for PNG with transparency)
            if pil_image.mode in ("RGBA", "P"):
                pil_image = pil_image.convert("RGB")

            # Calculate new dimensions (max_size on longest side)
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
            pil_image.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)

            # Save resized image to storage
            resized_file = ContentFile(output.getvalue())
            default_storage.save(resized_path, resized_file)

            # Return resized image
            output.seek(0)
            response = HttpResponse(
                output.getvalue(),
                content_type="image/jpeg",
            )
            response["Content-Disposition"] = (
                f'inline; filename="{Path(resized_path).name}"'
            )
            return response

    @action(detail=True, methods=["get"], url_path="preview")
    def get_preview_image(self, request, pk=None):
        """Get a preview (scaled-down) version of the image."""
        image = self.get_object()
        return self._generate_resized_image(
            image,
            max_size=1600,
            quality=85,
            suffix="preview",
        )

    @action(detail=True, methods=["get"], url_path="thumbnail")
    def get_thumbnail_image(self, request, pk=None):
        """Get a thumbnail (small) version of the image."""
        image = self.get_object()
        return self._generate_resized_image(
            image,
            max_size=400,
            quality=90,
            suffix="thumbnail",
        )
