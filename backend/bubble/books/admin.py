from django.contrib import admin

from .models import Author, Book, Genre, Publisher, Shelf


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "website")
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "parent_genre")
    search_fields = ("name",)
    list_filter = ("parent_genre",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("name", "isbn", "status", "created_at")
    search_fields = ("name", "isbn")
    list_filter = ("status", "category")
    raw_id_fields = ("verlag", "shelf")
    filter_horizontal = ("authors", "genres")
