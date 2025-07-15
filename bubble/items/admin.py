from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Image, Item, ItemCategory


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "emoji",
        "get_hierarchy_display",
        "parent_category",
        "ordering",
        "description",
    )
    list_filter = ("parent_category",)
    search_fields = (
        "name",
        "description",
    )
    ordering = ("ordering", "parent_category__name", "name")
    autocomplete_fields = ("parent_category",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "emoji",
                    "parent_category",
                    "description",
                    "ordering",
                ),
            },
        ),
    )

    @admin.display(
        description="Category Hierarchy",
        ordering="name",
    )
    def get_hierarchy_display(self, obj):
        hierarchy = obj.get_hierarchy()
        parts = hierarchy.split(" > ")
        if len(parts) > 1:
            parent_parts = " > ".join(parts[:-1])
            return format_html(
                '<span style="color: #888;">{}</span> > <strong>{}</strong>',
                parent_parts,
                parts[-1],
            )
        return format_html("<strong>{}</strong>", hierarchy)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent_category")


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
            _("Internal Options"),
            {
                "fields": ("internal", "payment_enabled"),
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
