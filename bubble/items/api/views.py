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
    CategorySelect2Serializer,
    CategorySerializer,
    CategoryTreeSerializer,
    ImageSerializer,
    ItemListSerializer,
    ItemSerializer,
)
from bubble.items.models import Image, Item, ItemCategory


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
        """Return items that the user can access and that he owns."""
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
        """Get only public items (not internal)."""
        queryset = (
            Item.objects.filter(internal=False, active=True)
            .select_related("user", "category")
            .prefetch_related("images")
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reorder_images(self, request, pk=None):
        """Reorder images for an item."""
        item = self.get_object()

        # Check if the user owns the item
        if item.user != request.user:
            return Response({"error": "Permission denied"}, status=403)

        image_order = request.data.get("image_order", [])

        if not isinstance(image_order, list):
            return Response({"error": "image_order must be a list"}, status=400)

        # Validate that all image IDs belong to this item
        item_image_ids = {str(img.id) for img in item.images.all()}
        provided_image_ids = {str(img_id) for img_id in image_order}

        if not provided_image_ids.issubset(item_image_ids):
            return Response({"error": "Invalid image IDs provided"}, status=400)

        # Update the ordering of each image
        for index, image_id in enumerate(image_order):
            Image.objects.filter(id=image_id, item=item).update(ordering=index)

        return Response({"success": True})


class ImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving images.
    Only authenticated users can access images.
    Users can only see images of items they have access to.
    """

    serializer_class = ImageSerializer
    permission_classes = [permissions.AllowAny]

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
            max_size=300,
            quality=80,
            suffix="thumbnail",
        )
