from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Image, Item


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1
    fields = ("original", "ordering")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "category",
        "active",
        "date_created",
    )
    list_filter = ("active", "category", "date_created")
    search_fields = ("name", "description", "user__username", "category__name")
    ordering = ("-date_created",)
    autocomplete_fields = ("user", "category")
    readonly_fields = ("date_created", "date_updated")
    inlines = [ImageInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "description", "user", "category", "active"),
            },
        ),
        (
            _("Custom Fields"),
            {
                "fields": ("custom_fields",),
                "classes": ("collapse",),
                "description": _("Category-specific additional fields stored as JSON"),
            },
        ),
        (
            _("Internal Options"),
            {
                "fields": ("intern",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("date_created", "date_updated"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("item", "filename", "ordering")
    list_filter = ("item__category",)
    search_fields = ("item__name",)
    ordering = ("item", "ordering")
