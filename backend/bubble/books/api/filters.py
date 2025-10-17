"""FilterSet definitions for Books API endpoints."""

import django_filters
from django.db.models import Q

from bubble.books.models import Author, Book, Genre, Publisher, Shelf


class AuthorFilter(django_filters.FilterSet):
    """Filter authors by common query parameters."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Author
        fields = ["name"]

    def filter_search(self, queryset, name, value):
        """Search in name and bio."""
        return queryset.filter(Q(name__icontains=value) | Q(bio__icontains=value))


class GenreFilter(django_filters.FilterSet):
    """Filter genres by common query parameters."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    parent_genre = django_filters.NumberFilter(field_name="parent_genre__id")
    has_parent = django_filters.BooleanFilter(method="filter_has_parent")

    class Meta:
        model = Genre
        fields = ["name", "parent_genre"]

    def filter_has_parent(self, queryset, name, value):
        """Filter genres with or without parent."""
        if value:
            return queryset.filter(parent_genre__isnull=False)
        return queryset.filter(parent_genre__isnull=True)


class PublisherFilter(django_filters.FilterSet):
    """Filter publishers by common query parameters."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Publisher
        fields = ["name"]

    def filter_search(self, queryset, name, value):
        """Search in name and description."""
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class ShelfFilter(django_filters.FilterSet):
    """Filter shelves by common query parameters."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Shelf
        fields = ["name"]

    def filter_search(self, queryset, name, value):
        """Search in name and description."""
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class BookFilter(django_filters.FilterSet):
    """Filter books by common query parameters."""

    isbn = django_filters.CharFilter(lookup_expr="iexact")
    author = django_filters.NumberFilter(field_name="authors__id")
    author_name = django_filters.CharFilter(
        field_name="authors__name", lookup_expr="icontains"
    )
    genre = django_filters.NumberFilter(field_name="genres__id")
    genre_name = django_filters.CharFilter(
        field_name="genres__name", lookup_expr="icontains"
    )
    publisher = django_filters.NumberFilter(field_name="verlag__id")
    publisher_name = django_filters.CharFilter(
        field_name="verlag__name", lookup_expr="icontains"
    )
    shelf = django_filters.NumberFilter(field_name="shelf__id")
    shelf_name = django_filters.CharFilter(
        field_name="shelf__name", lookup_expr="icontains"
    )
    year = django_filters.NumberFilter()
    year_min = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    year_max = django_filters.NumberFilter(field_name="year", lookup_expr="lte")
    topic = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Book
        fields = [
            "isbn",
            "author",
            "author_name",
            "genre",
            "genre_name",
            "publisher",
            "publisher_name",
            "shelf",
            "shelf_name",
            "year",
            "year_min",
            "year_max",
            "topic",
        ]
