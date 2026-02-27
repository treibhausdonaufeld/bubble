"""Serializers for collections API."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm
from rest_framework import serializers

from bubble.collections.models import Collection, CollectionItem
from bubble.items.api.serializers import ItemMinimalSerializer

User = get_user_model()


class CollectionItemSerializer(serializers.ModelSerializer):
    """Serializer for CollectionItem model."""

    item = ItemMinimalSerializer(read_only=True)
    item_id = serializers.UUIDField(write_only=True)
    added_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CollectionItem
        fields = [
            "id",
            "collection",
            "item",
            "item_id",
            "added_at",
            "added_by",
            "note",
            "ordering",
        ]
        read_only_fields = ["id", "collection", "added_at", "added_by"]

    def validate_item_id(self, value):
        """Ensure user has permission to view the item."""
        request = self.context.get("request")
        if request and request.user:
            # Check if user can view this item
            viewable_items = get_objects_for_user(
                request.user, "items.view_item", accept_global_perms=False
            )
            if not viewable_items.filter(pk=value).exists():
                raise serializers.ValidationError(
                    _("You don't have permission to add this item.")
                )
        return value


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model."""

    owner = serializers.StringRelatedField(read_only=True)
    items_count = serializers.SerializerMethodField()
    collection_items = CollectionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "items_count",
            "collection_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_items_count(self, obj):
        """Get the number of items in the collection."""
        return obj.items.count()


class CollectionListSerializer(CollectionSerializer):
    """Lightweight serializer for collection lists."""

    collection_items = None

    class Meta(CollectionSerializer.Meta):
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "items_count",
            "created_at",
            "updated_at",
        ]


class CollectionPermissionSerializer(serializers.Serializer):
    """Serializer for managing collection permissions."""

    user_id = serializers.IntegerField(required=False, allow_null=True)
    group_id = serializers.IntegerField(required=False, allow_null=True)
    permission = serializers.ChoiceField(
        choices=[
            "view_collection",
            "change_collection",
            "add_items",
            "remove_items",
        ]
    )
    action = serializers.ChoiceField(choices=["grant", "revoke"])

    def validate(self, attrs):
        """Ensure either user_id or group_id is provided, but not both."""
        user_id = attrs.get("user_id")
        group_id = attrs.get("group_id")

        if not user_id and not group_id:
            raise serializers.ValidationError(
                _("Either user_id or group_id must be provided.")
            )

        if user_id and group_id:
            raise serializers.ValidationError(
                _("Cannot specify both user_id and group_id.")
            )

        # Validate user exists
        if user_id:
            try:
                User.objects.get(pk=user_id)
            except User.DoesNotExist as e:
                raise serializers.ValidationError(
                    {"user_id": _("User not found.")}
                ) from e

        # Validate group exists
        if group_id:
            try:
                Group.objects.get(pk=group_id)
            except Group.DoesNotExist as e:
                raise serializers.ValidationError(
                    {"group_id": _("Group not found.")}
                ) from e

        return attrs

    def save(self, collection):
        """Apply the permission change."""
        user_id = self.validated_data.get("user_id")
        group_id = self.validated_data.get("group_id")
        permission = f"collections.{self.validated_data['permission']}"
        action = self.validated_data["action"]

        if user_id:
            user = User.objects.get(pk=user_id)
            if action == "grant":
                assign_perm(permission, user, collection)
            else:
                remove_perm(permission, user, collection)
        elif group_id:
            group = Group.objects.get(pk=group_id)
            if action == "grant":
                assign_perm(permission, group, collection)
            else:
                remove_perm(permission, group, collection)

        return collection
