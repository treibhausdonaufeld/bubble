"""FilterSet definitions for Item API endpoints."""

from __future__ import annotations

import logging

import django_filters
from django.db.models import Q, QuerySet
from pgvector.django import CosineDistance

from bubble.items.embeddings import get_embedding_model
from bubble.items.models import Item, ItemEmbedding, StatusType

logger = logging.getLogger(__name__)


class ItemFilter(django_filters.FilterSet):
    """Filter items by common query parameters.

    Supported query params:
    - status: multiple choice filter for status integers
    - category: exact category value
    - published: boolean; if true restrict to published statuses
    - min_sale_price / max_sale_price: numeric range for sale_price
    - min_rental_price / max_rental_price: numeric range for rental_price
    - user: user id for owner filtering
    - search: substring match on name or description (case-insensitive)
    - created_after / created_before: ISO8601 datetime filtering
    """

    status = django_filters.MultipleChoiceFilter(
        choices=StatusType.choices,
        field_name="status",
        conjoined=False,  # OR logic for multiple values
    )

    published = django_filters.BooleanFilter(method="filter_published")

    # Price range filters (these are already optimal)
    min_sale_price = django_filters.NumberFilter(
        field_name="sale_price", lookup_expr="gte"
    )
    max_sale_price = django_filters.NumberFilter(
        field_name="sale_price", lookup_expr="lte"
    )
    min_rental_price = django_filters.NumberFilter(
        field_name="rental_price", lookup_expr="gte"
    )
    max_rental_price = django_filters.NumberFilter(
        field_name="rental_price", lookup_expr="lte"
    )

    # Use built-in search filter
    search = django_filters.CharFilter(method="filter_search")

    # Use built-in datetime filters
    created_after = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Item
        fields = {
            "category": ["exact"],
            "user": ["exact"],  # Allow filtering by user ID
        }

    def filter_published(
        self,
        queryset: QuerySet[Item],
        name: str,
        value: bool,  # noqa: FBT001
    ):
        """Filter for published status based on StatusType.published()."""
        if value is None:
            return queryset
        if value:
            return queryset.filter(status__in=StatusType.published())
        # if explicitly false, exclude published statuses
        return queryset.exclude(status__in=StatusType.published())

    def filter_search(self, queryset: QuerySet[Item], name: str, value: str):
        """Search in name and description fields."""
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )

    def semantic_search(self, queryset: QuerySet[Item], name: str, value: str):
        """Not yet enabled..."""
        model = get_embedding_model()
        query_embedding = model.encode(value, convert_to_numpy=True).tolist()

        # Use cosine distance for similarity (lower distance = more similar)
        # Filter out items without embeddings

        embeddings_qs = ItemEmbedding.objects.filter(vector__isnull=False).annotate(
            distance=CosineDistance("vector", query_embedding)
        )

        return queryset.filter(pk__in=embeddings_qs.values_list("pk", flat=True))
