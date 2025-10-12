"""Serializers for books API."""

from rest_framework import serializers

from bubble.books.models import Author, Book, Genre, Publisher, Shelf
from bubble.items.api.serializers import ItemListSerializer, ItemSerializer


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model."""

    books_count = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            "uuid",
            "name",
            "website",
            "bio",
            "books_count",
        ]
        read_only_fields = ["uuid"]

    def get_books_count(self, obj):
        """Get the number of books by this author."""
        return obj.books.count()


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genre model."""

    parent_genre_name = serializers.CharField(
        source="parent_genre.name", read_only=True, allow_null=True
    )
    parent_genre_uuid = serializers.UUIDField(
        source="parent_genre.uuid", read_only=True, allow_null=True
    )
    hierarchy = serializers.CharField(source="get_hierarchy", read_only=True)
    books_count = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = [
            "uuid",
            "name",
            "description",
            "parent_genre",
            "parent_genre_name",
            "parent_genre_uuid",
            "hierarchy",
            "books_count",
        ]
        read_only_fields = ["uuid"]

    def get_books_count(self, obj):
        """Get the number of books in this genre."""
        return obj.books.count()


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for Publisher model."""

    books_count = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = [
            "uuid",
            "name",
            "description",
            "books_count",
        ]
        read_only_fields = ["uuid"]

    def get_books_count(self, obj):
        """Get the number of books from this publisher."""
        return obj.books.count()


class ShelfSerializer(serializers.ModelSerializer):
    """Serializer for Shelf model."""

    books_count = serializers.SerializerMethodField()

    class Meta:
        model = Shelf
        fields = [
            "uuid",
            "name",
            "description",
            "books_count",
        ]
        read_only_fields = ["uuid"]

    def get_books_count(self, obj):
        """Get the number of books on this shelf."""
        return obj.books.count()


class BookListSerializer(ItemListSerializer):
    """Serializer for Book list view."""

    authors = serializers.StringRelatedField(many=True, read_only=True)
    genres = serializers.StringRelatedField(many=True, read_only=True)
    verlag_name = serializers.CharField(source="verlag.name", read_only=True)
    shelf_name = serializers.CharField(source="shelf.name", read_only=True)

    class Meta(ItemListSerializer.Meta):
        model = Book
        exclude = ["id"]


class BookSerializer(ItemSerializer):
    """Serializer for Book detail view."""

    authors = AuthorSerializer(many=True, read_only=True)
    author_uuids = serializers.SlugRelatedField(
        many=True,
        slug_field="uuid",
        queryset=Author.objects.all(),
        write_only=True,
        source="authors",
        required=False,
    )

    genres = GenreSerializer(many=True, read_only=True)
    genre_uuids = serializers.SlugRelatedField(
        many=True,
        slug_field="uuid",
        queryset=Genre.objects.all(),
        write_only=True,
        source="genres",
        required=False,
    )

    verlag = PublisherSerializer(read_only=True)
    verlag_uuid = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Publisher.objects.all(),
        write_only=True,
        source="verlag",
        required=False,
        allow_null=True,
    )

    shelf = ShelfSerializer(read_only=True)
    shelf_uuid = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Shelf.objects.all(),
        write_only=True,
        source="shelf",
        required=False,
        allow_null=True,
    )

    class Meta(ItemSerializer.Meta):
        model = Book
        exclude = ["id"]
