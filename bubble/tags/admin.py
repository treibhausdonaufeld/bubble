from django.contrib import admin

from .models import ItemTag


@admin.register(ItemTag)
class ItemTagAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)
