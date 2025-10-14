"""API views for books."""

import requests
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    DjangoModelPermissions,
    DjangoModelPermissionsOrAnonReadOnly,
)
from rest_framework.response import Response

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
from bubble.books.services import OpenLibraryService
from bubble.items.models import Item


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

    Dynamically includes both Book instances and Items with category='books'.
    When an Item with category='books' is accessed, it's automatically promoted
    to a Book instance via signals.

    list: Get all books
    retrieve: Get a specific book by UUID
    create: Create a new book
    update: Update a book
    partial_update: Partially update a book
    destroy: Delete a book
    """

    serializer_class = BookSerializer
    permission_classes = [DjangoModelPermissions]
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

    def get_queryset(self):
        return (
            Book.objects.get_for_user(self.request.user)
            .select_related("user", "verlag", "shelf")
            .prefetch_related("authors", "genres", "images")
        )

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == "list":
            return BookListSerializer
        return BookSerializer

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        try:
            obj = super().get_object()
        except Http404:
            try:
                item = Item.objects.get(uuid=self.kwargs[lookup_url_kwarg])
                # Create temporary book instance for response
                obj = Book(item_ptr_id=item.pk)
                obj.__dict__.update(item.__dict__)
                self.check_object_permissions(self.request, obj)
            except Item.DoesNotExist:
                msg = "No Book or Item matches the given query."
                raise Http404(msg) from None

        return obj

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "isbn": {
                        "type": "string",
                        "description": (
                            "ISBN number to fetch book details from "
                            "OpenLibrary API. If not provided, uses the "
                            "book's existing ISBN."
                        ),
                        "example": "9780980200447",
                    }
                },
            }
        },
        responses={200: BookSerializer},
    )
    @action(detail=True, methods=["put"])
    def isbn_update(self, request, uuid=None):
        """
        Update book details from OpenLibrary based on ISBN.

        Optionally provide an ISBN in the request body to update the book with data
        from OpenLibrary. If no ISBN is provided, the book's existing ISBN will be used.
        """
        book = self.get_object()
        isbn = request.data.get("isbn")

        if not isbn and not book.isbn:
            return Response(
                {"error": "Book does not have an ISBN and none was provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = OpenLibraryService()
        try:
            service.update_book_from_isbn(book, isbn=isbn)
        except requests.RequestException as e:
            return Response(
                {"error": f"Failed to fetch data from OpenLibrary: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        serializer = self.get_serializer(book)
        return Response(serializer.data)
