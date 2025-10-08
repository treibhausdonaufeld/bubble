from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedInlineAdminMixin, GuardedModelAdminMixin
from simple_history.admin import SimpleHistoryAdmin

from .models import Image, Item


class ImageInline(GuardedInlineAdminMixin, admin.TabularInline):
    model = Image
    extra = 1
    fields = ("original", "ordering")


@admin.register(Item)
class ItemAdmin(GuardedModelAdminMixin, SimpleHistoryAdmin):
    list_display = (
        "name",
        "user",
        "category",
        "condition",
        "status",
        "sale_price",
        "rental_price",
        "created_at",
    )
    list_filter = ("condition", "category", "created_at")
    search_fields = ("name", "description", "user__username", "category__name")
    ordering = ("-created_at",)
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ImageInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "user",
                    "category",
                    "active",
                    "status",
                ),
            },
        ),
        (
            _("Item Details"),
            {
                "fields": (
                    "condition",
                    "sale_price",
                    "rental_price",
                    "display_contact",
                ),
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
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
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
