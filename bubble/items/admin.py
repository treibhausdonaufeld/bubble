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
        "item_type",
        "price",
        "active",
        "date_created",
    )
    list_filter = ("active", "item_type", "category", "date_created")
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
            _("Item Details"),
            {
                "fields": ("item_type", "price", "display_contact"),
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
                "fields": ("internal", "payment_enabled"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Media"),
            {
                "fields": ("profile_img_frame", "profile_img_frame_alt"),
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
