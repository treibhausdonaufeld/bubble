from django.contrib import admin
from django.utils.html import format_html

from bubble.categories.models import ItemCategory


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "get_hierarchy_display", "parent_category", "description")
    list_filter = ("parent_category",)
    search_fields = ("name", "description", "prompt_name", "prompt_description")
    ordering = ("parent_category__name", "name")
    autocomplete_fields = ("parent_category",)

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "parent_category", "description"),
            },
        ),
        (
            "AI Prompts",
            {
                "fields": ("prompt_name", "prompt_description"),
                "classes": ("collapse",),
                "description": "Optional fields for AI-generated content",
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
