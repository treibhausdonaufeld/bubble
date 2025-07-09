import json

from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from bubble.categories.models import ItemCategory


class PrettyJSONWidget(forms.Textarea):
    """A widget that displays JSON in a pretty, editable format"""

    def __init__(self, attrs=None):
        default_attrs = {
            "style": "font-family: monospace; font-size: 12px; line-height: 1.4;",
            "rows": 20,
            "cols": 80,
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if value is None:
            return None

        try:
            # If it's a string, try to parse and pretty-print it
            if isinstance(value, str):
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            # If it's already a dict/list, pretty-print it
            return json.dumps(value, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return value


class ItemCategoryAdminForm(forms.ModelForm):
    """Custom form with better widgets for ItemCategory"""

    # Use SimpleArrayField for better array handling
    filters = SimpleArrayField(
        forms.CharField(max_length=50),
        delimiter=",",
        required=False,
        widget=forms.TextInput(
            attrs={
                "style": "width: 600px;",
                "placeholder": "e.g., type, price, condition (comma-separated)",
            },
        ),
    )

    sort_by = SimpleArrayField(
        forms.CharField(max_length=50),
        delimiter=",",
        required=False,
        widget=forms.TextInput(
            attrs={
                "style": "width: 600px;",
                "placeholder": "e.g., price, created_at, name (comma-separated)",
            },
        ),
    )

    class Meta:
        model = ItemCategory
        fields = [
            "name",
            "parent_category",
            "description",
            "emoji",
            "url_slug",
            "filters",
            "sort_by",
            "upper_tag",
            "lower_tag",
            "custom_fields",
            "ordering",
        ]
        widgets = {
            "custom_fields": PrettyJSONWidget(),
            "description": forms.Textarea(attrs={"rows": 4, "cols": 80}),
            "prompt_name": forms.Textarea(attrs={"rows": 3, "cols": 80}),
            "prompt_description": forms.Textarea(attrs={"rows": 5, "cols": 80}),
            "upper_tag": forms.TextInput(attrs={"style": "width: 300px;"}),
            "lower_tag": forms.TextInput(attrs={"style": "width: 300px;"}),
            "url_slug": forms.TextInput(attrs={"style": "width: 300px;"}),
        }

    def clean_custom_fields(self):
        """Validate and format the JSON field"""
        data = self.cleaned_data.get("custom_fields")

        if not data:
            return {}

        try:
            # If it's a string, parse it
            if isinstance(data, str):
                data = json.loads(data)

            # Validate the structure
            if not isinstance(data, dict):
                msg = "Custom fields must be a JSON object"
                raise forms.ValidationError(msg)

            # Optional: Add more specific validation here
            for field_name, field_config in data.items():
                if not isinstance(field_config, dict):
                    msg = f"Field '{field_name}' must be an object"
                    raise forms.ValidationError(msg)

                if "type" not in field_config:
                    msg = f"Field '{field_name}' must have a 'type'"
                    raise forms.ValidationError(msg)

                # Validate field types
                valid_types = [
                    "text",
                    "choice",
                    "number",
                    "date",
                    "boolean",
                    "textarea",
                ]
                if field_config["type"] not in valid_types:
                    msg = (
                        f"Field '{field_name}' has invalid type. "
                        f"Valid types are: {', '.join(valid_types)}"
                    )
                    raise forms.ValidationError(msg)

            return data

        except json.JSONDecodeError as e:
            msg = f"Invalid JSON: {e!s}"
            raise forms.ValidationError(msg) from e


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    form = ItemCategoryAdminForm

    list_display = (
        "name",
        "emoji",
        "get_hierarchy_display",
        "parent_category",
        "url_slug",
        "ordering",
        "get_filters_display",
        "get_sort_display",
        "get_tags_display",
    )
    list_filter = ("parent_category",)
    search_fields = (
        "name",
        "description",
        "prompt_name",
        "prompt_description",
        "url_slug",
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
        (
            "Content Type Configuration",
            {
                "fields": ("url_slug", "custom_fields"),
                "description": "Configure URL slug and dynamic fields",
            },
        ),
        (
            "Display and Filter Configuration",
            {
                "fields": ("filters", "sort_by", "upper_tag", "lower_tag"),
                "description": "Configure which fields appear as filters, sorting options, and item card display",
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

    @admin.display(description="Filters")
    def get_filters_display(self, obj):
        if obj.filters:
            return ", ".join(obj.filters[:3])
        return "-"

    @admin.display(description="Sort By")
    def get_sort_display(self, obj):
        if obj.sort_by:
            return ", ".join(obj.sort_by[:3])
        return "-"

    @admin.display(description="Display Tags")
    def get_tags_display(self, obj):
        tags = []
        if obj.upper_tag:
            tags.append(f"↑{obj.upper_tag}")
        if obj.lower_tag:
            tags.append(f"↓{obj.lower_tag}")
        return " | ".join(tags) if tags else "-"

    class Media:
        css = {
            "all": ("admin/css/forms.css",),
        }
        js = ("admin/js/jquery.init.js",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Add detailed help text for custom_fields
        help_text_html = """
            <div style="margin-top: 10px; padding: 10px; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px;">
                <strong>JSON Schema Examples:</strong><br><br>

                <strong>Simple fields:</strong><br>
                <pre style="margin: 5px 0; font-size: 11px;">{{
  "field_name": {{
    "type": "text",
    "label": "Field Label",
    "required": true
  }}
}}</pre>

                <strong>Choice field:</strong><br>
                <pre style="margin: 5px 0; font-size: 11px;">{{
  "size": {{
    "type": "choice",
    "label": "Size",
    "choices": ["S", "M", "L", "XL"],
    "required": true
  }}
}}</pre>

                <strong>Dependent field with array values (shows for multiple conditions):</strong><br>
                <pre style="margin: 5px 0; font-size: 11px;">{{
  "device_type": {{
    "type": "choice",
    "label": "Typ",
    "choices": ["laptop", "desktop", "smartphone", "tablet"],
    "required": true
  }},
  "screen_size": {{
    "type": "choice",
    "label": "Bildschirmgröße",
    "choices": ["13\"", "15\"", "17\"", "24\"", "27\""],
    "depending": "device_type",
    "depending_values": ["laptop", "desktop"]  // Shows for both
  }}
}}</pre>

                <strong>Field with default value:</strong><br>
                <pre style="margin: 5px 0; font-size: 11px;">{{
  "condition": {{
    "type": "choice",
    "label": "Zustand",
    "choices": ["new", "used", "defective"],
    "default": "used",  // Default value if not specified
    "required": true
  }},
  "quantity": {{
    "type": "number",
    "label": "Anzahl",
    "default": 1,  // Default to 1
    "required": false
  }}
}}</pre>

                <strong>Valid field types:</strong> text, choice, number, date, boolean, textarea
            </div>
        """
        form.base_fields["custom_fields"].help_text = mark_safe(help_text_html)

        return form
