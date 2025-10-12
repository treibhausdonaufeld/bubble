"""API views for books."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from bubble.books.api.filters import (
    AuthorFilter,
    BookFilter,
    GenreFilter,
    PublisherFilter,
    ShelfFilter,
)
from bubble.books.api.serializers import (
    AuthorSerializer,
    BookListSerializer,
    BookSerializer,
    GenreSerializer,
    PublisherSerializer,
    ShelfSerializer,
)
from bubble.books.models import Author, Book, Genre, Publisher, Shelf


class AuthorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing authors.

    list: Get all authors
    retrieve: Get a specific author by UUID
    create: Create a new author
    update: Update an author
    partial_update: Partially update an author
    destroy: Delete an author
    """

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "uuid"
    filterset_class = AuthorFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "bio"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]


class GenreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing genres.

    list: Get all genres
    retrieve: Get a specific genre by UUID
    create: Create a new genre
    update: Update a genre
    partial_update: Partially update a genre
    destroy: Delete a genre
    """

    queryset = Genre.objects.all().select_related("parent_genre")
    serializer_class = GenreSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "uuid"
    filterset_class = GenreFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]


class PublisherViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing publishers.

    list: Get all publishers
    retrieve: Get a specific publisher by UUID
    create: Create a new publisher
    update: Update a publisher
    partial_update: Partially update a publisher
    destroy: Delete a publisher
    """

    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "uuid"
    filterset_class = PublisherFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]


class ShelfViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shelves.

    list: Get all shelves
    retrieve: Get a specific shelf by UUID
    create: Create a new shelf
    update: Update a shelf
    partial_update: Partially update a shelf
    destroy: Delete a shelf
    """

    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "uuid"
    filterset_class = ShelfFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books.

    list: Get all books
    retrieve: Get a specific book by UUID
    create: Create a new book
    update: Update a book
    partial_update: Partially update a book
    destroy: Delete a book
    """

    queryset = (
        Book.objects.all()
        .select_related("user", "verlag", "shelf")
        .prefetch_related("authors", "genres", "images")
    )
    serializer_class = BookSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "uuid"
    filterset_class = BookFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "description", "isbn", "topic"]
    ordering_fields = ["created_at", "updated_at", "year", "name"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == "list":
            return BookListSerializer
        return BookSerializer
