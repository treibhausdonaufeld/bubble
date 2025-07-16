from django.contrib import admin

from .models import Favorite, FavoriteList


@admin.register(FavoriteList)
class FavoriteListAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "is_default", "created_at", "favorite_count"]
    list_filter = ["is_default", "created_at"]
    search_fields = ["name", "user__username"]
    ordering = ["-created_at"]
    filter_horizontal = ["shared_with", "editors"]

    @admin.display(description="Favorites Count")
    def favorite_count(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "url", "favorite_list", "created_at"]
    list_filter = ["created_at", "favorite_list"]
    search_fields = ["user__username", "title", "url", "favorite_list__name"]
    ordering = ["-created_at"]
