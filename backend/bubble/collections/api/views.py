"""API views for collections."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bubble.collections.api.permissions import (
    CanManagePermissions,
    CollectionObjectPermission,
)
from bubble.collections.api.serializers import (
    CollectionItemSerializer,
    CollectionListSerializer,
    CollectionPermissionSerializer,
    CollectionSerializer,
)
from bubble.collections.models import Collection, CollectionItem
from bubble.items.models import Item


class CollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing collections.

    Provides CRUD operations for collections with object-level permissions.
    """

    lookup_field = "id"
    permission_classes = [IsAuthenticated, CollectionObjectPermission]

    def get_queryset(self):
        """Return collections the user has permission to view."""
        return Collection.objects.get_for_user(self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == "list":
            return CollectionListSerializer
        return CollectionSerializer

    def perform_create(self, serializer):
        """Set the owner to the current user."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, pk=None):
        """Add an item to the collection."""
        collection = self.get_object()

        # Create CollectionItem
        serializer = CollectionItemSerializer(
            data={**request.data, "collection": collection.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            item = Item.objects.get(pk=serializer.validated_data["item_id"])
            collection_item = CollectionItem.objects.create(
                collection=collection,
                item=item,
                added_by=request.user,
                note=serializer.validated_data.get("note", ""),
                ordering=serializer.validated_data.get("ordering", 0),
            )

        return Response(
            CollectionItemSerializer(
                collection_item, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="bulk-add-items",
    )
    def bulk_add_items(self, request, pk=None):
        """Add multiple items to the collection."""
        collection = self.get_object()
        item_ids = request.data.get("item_ids", [])

        if not isinstance(item_ids, list):
            return Response(
                {"error": _("item_ids must be a list")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        added_items = []
        errors = []

        with transaction.atomic():
            for item_id in item_ids:
                try:
                    item = Item.objects.get(pk=item_id)
                    # Check if item is already in collection
                    if CollectionItem.objects.filter(
                        collection=collection, item=item
                    ).exists():
                        errors.append(
                            {
                                "item_id": item_id,
                                "error": _("Item already in collection"),
                            }
                        )
                        continue

                    collection_item = CollectionItem.objects.create(
                        collection=collection,
                        item=item,
                        added_by=request.user,
                    )
                    added_items.append(collection_item)
                except Item.DoesNotExist:
                    errors.append({"item_id": item_id, "error": _("Item not found")})

        return Response(
            {
                "added": CollectionItemSerializer(
                    added_items, many=True, context={"request": request}
                ).data,
                "errors": errors,
            },
            status=status.HTTP_201_CREATED
            if added_items
            else status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="remove-item/(?P<item_id>[^/.]+)",
    )
    def remove_item(self, request, pk=None, item_id=None):
        """Remove an item from the collection."""
        collection = self.get_object()

        try:
            collection_item = CollectionItem.objects.get(
                collection=collection, item_id=item_id
            )
            collection_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CollectionItem.DoesNotExist:
            return Response(
                {"error": _("Item not found in collection")},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"], url_path="bulk-remove-items")
    def bulk_remove_items(self, request, pk=None):
        """Remove multiple items from the collection."""
        collection = self.get_object()
        item_ids = request.data.get("item_ids", [])

        if not isinstance(item_ids, list):
            return Response(
                {"error": _("item_ids must be a list")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count = CollectionItem.objects.filter(
            collection=collection, item_id__in=item_ids
        ).delete()[0]

        return Response({"deleted_count": deleted_count}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanManagePermissions],
    )
    def manage_permissions(self, request, pk=None):
        """
        Manage permissions for a collection.

        Only the owner can manage permissions.
        """
        collection = self.get_object()
        serializer = CollectionPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(collection)

        return Response(
            {"message": _("Permission updated successfully")},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="my-collections")
    def my_collections(self, request):
        """Get all collections owned by the current user."""
        collections = Collection.objects.filter(owner=request.user)
        serializer = CollectionListSerializer(
            collections, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CollectionItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items within collections.

    Provides CRUD operations for collection items.
    """

    lookup_field = "id"
    serializer_class = CollectionItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return collection items the user has permission to view."""
        # Get collections the user can view
        viewable_collections = Collection.objects.get_for_user(self.request.user)
        return CollectionItem.objects.filter(collection__in=viewable_collections)

    def perform_create(self, serializer):
        """Set the added_by to the current user."""
        collection = serializer.validated_data["collection"]
        if not self.request.user.has_perm("collections.add_items", collection):
            return Response(
                {
                    "error": _(
                        "You don't have permission to add items to this collection"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        item = Item.objects.get(pk=serializer.validated_data["item_id"])
        serializer.save(added_by=self.request.user, item=item)
        return None
