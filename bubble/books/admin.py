"""
Admin configuration for books app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Author, Genre, Location, Book


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'bio')
    search_fields = ('name', 'bio')
    ordering = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_genre', 'description')
    list_filter = ('parent_genre',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_authors_display', 'year', 'user', 'location', 'active', 'date_created')
    list_filter = ('active', 'year', 'location', 'genres', 'date_created')
    search_fields = ('title', 'description', 'topic', 'authors__name', 'user__username')
    filter_horizontal = ('authors', 'genres')
    readonly_fields = ('uuid', 'embedding', 'date_created', 'date_updated')
    ordering = ('-date_created',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'authors', 'year', 'topic', 'description')
        }),
        (_('Classification'), {
            'fields': ('genres', 'location', 'image')
        }),
        (_('System'), {
            'fields': ('user', 'active', 'internal', 'uuid', 'embedding'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        }),
    )
    
    def get_authors_display(self, obj):
        return obj.get_authors_display()
    get_authors_display.short_description = _('Authors')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.user = request.user
        super().save_model(request, obj, form, change)
