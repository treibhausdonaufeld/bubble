from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "photo_preview", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at", "photo_preview_large")

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "description"),
            },
        ),
        (
            _("Photo"),
            {
                "fields": ("photo", "photo_preview_large"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Photo"))
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" height="50" style="border-radius: 5px;" />',
                obj.photo.url,
            )
        return "-"

    @admin.display(description=_("Current Photo"))
    def photo_preview_large(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 5px;" />',
                obj.photo.url,
            )
        return _("No photo uploaded")
