from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bubble.categories.models import ItemCategory
from bubble.items.models import Image, Item


class ItemForm(forms.ModelForm):
    MIN_ITEM_NAME_LENGTH = 3

    # Category dropdown showing only leaf categories (lowest level)
    selected_category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),  # Empty queryset for AJAX loading
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select select2-category",
                "data-placeholder": _("Search and select a category..."),
            },
        ),
        label=_("Category"),
    )

    class Meta:
        model = Item
        fields = [
            "name",
            "description",
            "selected_category",
            "item_type",
            "price",
            "display_contact",
            "active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Item name")},
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Describe your item..."),
                },
            ),
            "item_type": forms.Select(attrs={"class": "form-select select2-field"}),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": _("Price in Euro"),
                },
            ),
            "display_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "item_type": _("Type"),
            "price": _("Price"),
            "display_contact": _("Show contact"),
            "active": _("Published"),
        }
        help_texts = {
            "display_contact": _("Check to display your contact information"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.root_category = kwargs.pop("root_category", None)
        super().__init__(*args, **kwargs)

        # Set initial value for selected_category when editing an item
        if (
            self.instance.pk
            and hasattr(self.instance, "category")
            and self.instance.category
        ):
            self.fields["selected_category"].initial = self.instance.category

        # Add dynamic fields based on category schema
        # For create form: use root_category, for edit form: use item's category
        if self.root_category or (
            hasattr(self.instance, "category") and self.instance.category
        ):
            self._add_dynamic_fields()

        # Add JavaScript data attributes for dynamic field generation
        if self.root_category:
            self.fields["selected_category"].widget.attrs.update(
                {
                    "data-root-category": self.root_category.id,
                    "data-url-slug": self.root_category.url_slug,
                },
            )

        # Add internal-only fields if user is internal
        if self.user and hasattr(self.user, "profile") and self.user.profile.internal:
            self.fields["internal"] = forms.BooleanField(
                required=False,
                initial=False,
                label=_("Internal"),
                widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                help_text=_("Check if this item is for internal use only"),
            )
            self.fields["payment_enabled"] = forms.BooleanField(
                required=False,
                initial=False,
                label=_("Treibhaus payment"),
                widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                help_text=_("Accept Treibhaus payment method"),
            )
            # Update Meta.fields to include internal fields
            self.Meta.fields = [*self.Meta.fields, "internal", "payment_enabled"]

    def clean_name(self):
        name: str | None = self.cleaned_data.get("name")
        if name and len(name) < self.MIN_ITEM_NAME_LENGTH:
            raise ValidationError(
                _("Item name must be at least %(min_length)d characters long.")
                % {"min_length": self.MIN_ITEM_NAME_LENGTH},
            )
        return name

    def clean_selected_category(self) -> ItemCategory | None:
        """Validate that the selected category exists and is a leaf category."""
        selected_category = self.cleaned_data.get("selected_category")

        if selected_category and not selected_category.is_leaf_category():
            raise ValidationError(
                _("Please select a specific category (not a general category)."),
            )

        return selected_category

    def _add_dynamic_fields(self):
        """Add dynamic fields based on category's field schema"""
        # Determine which category to use for schema
        if hasattr(self.instance, "category") and self.instance.category:
            # Editing existing item - use item's category
            root_category = self.instance.category.get_root_category()
        elif self.root_category:
            # Creating new item - use provided root category
            root_category = self.root_category
        else:
            return

        # Add custom fields
        for field_name, field_config in root_category.custom_fields.items():
            is_required = field_config.get("required", False)
            self._create_dynamic_field(field_name, field_config, required=is_required)

    def _create_dynamic_field(self, field_name, field_config, *, required=False):
        """Create a form field based on configuration"""
        field_type = field_config.get("type", "text")
        label = field_config.get("label", field_name)

        # Get existing value from custom_fields if editing
        initial_value = None
        if self.instance.pk and self.instance.custom_fields:
            field_data = self.instance.custom_fields.get(field_name)
            if isinstance(field_data, dict) and "value" in field_data:
                initial_value = field_data["value"]
            else:
                # Handle old format for backward compatibility
                initial_value = field_data

        # No longer skip status field since it's now handled as custom field

        # Create appropriate field based on type
        if field_type == "text":
            field = forms.CharField(
                label=label,
                required=required,
                initial=initial_value,
                widget=forms.TextInput(attrs={"class": "form-control"}),
            )
        elif field_type == "textarea":
            field = forms.CharField(
                label=label,
                required=required,
                initial=initial_value,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            )
        elif field_type == "number":
            field = forms.IntegerField(
                label=label,
                required=required,
                initial=initial_value,
                widget=forms.NumberInput(attrs={"class": "form-control"}),
            )
        elif field_type == "choice":
            # Support both simple list and key-value pairs for choices
            raw_choices = field_config.get("choices", [])
            choices = []

            for choice in raw_choices:
                if isinstance(choice, dict):
                    # Key-value format: {"key": "db_value", "value": "display_value"}
                    key = choice.get("key", "")
                    value = choice.get(
                        "value",
                        key,
                    )  # Fall back to key if value not provided
                    choices.append((key, value))
                else:
                    # Simple format: just use the value for both key and display
                    choices.append((choice, choice))

            field = forms.ChoiceField(
                label=label,
                required=required,
                choices=choices,
                initial=initial_value,
                widget=forms.Select(attrs={"class": "form-select select2-field"}),
            )
        elif field_type == "datetime":
            field = forms.DateTimeField(
                label=label,
                required=required,
                initial=initial_value,
                widget=forms.DateTimeInput(
                    attrs={
                        "class": "form-control",
                        "type": "datetime-local",
                    },
                ),
            )
        else:
            # Default to text field
            field = forms.CharField(
                label=label,
                required=required,
                initial=initial_value,
                widget=forms.TextInput(attrs={"class": "form-control"}),
            )

        # Add field to form
        self.fields[f"custom_{field_name}"] = field

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}

        selected_category = cleaned_data.get("selected_category")

        # Set the final category
        cleaned_data["category"] = selected_category

        # Collect custom field values with labels
        custom_values = {}
        if selected_category:
            root_category = selected_category.get_root_category()

            for field_name, field_config in root_category.custom_fields.items():
                custom_field_name = f"custom_{field_name}"
                if custom_field_name in cleaned_data:
                    value = cleaned_data[custom_field_name]
                    # Store both value and label
                    custom_values[field_name] = {
                        "value": value,
                        "label": field_config.get("label", field_name.title()),
                    }

        cleaned_data["custom_field_values"] = custom_values
        return cleaned_data

    def save(self, *, commit: bool = True):
        instance = super().save(commit=False)

        if self.user:
            instance.user = self.user

        # Set the category from cascading dropdowns
        category = self.cleaned_data.get("category")
        if category:
            instance.category = category

        # Set custom field values
        custom_values = self.cleaned_data.get("custom_field_values", {})
        if custom_values:
            # Merge with existing custom_fields to preserve other data
            if not instance.custom_fields:
                instance.custom_fields = {}
            instance.custom_fields.update(custom_values)

        # Set default values for internal-only fields if user is not internal
        if not (
            self.user and hasattr(self.user, "profile") and self.user.profile.internal
        ):
            instance.internal = False
            instance.payment_enabled = False

        if commit:
            instance.save()

        return instance


class ItemFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control search-input",
                "placeholder": _("Search items, tags, categories..."),
            },
        ),
    )

    # Category filters with hierarchy support
    parent_category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.filter(parent_category=None),
        required=False,
        empty_label=_("All categories"),
        widget=forms.Select(
            attrs={"class": "form-select category-filter", "id": "parent-category"},
        ),
    )

    subcategory = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        empty_label=_("All subcategories"),
        widget=forms.Select(
            attrs={"class": "form-select category-filter", "id": "subcategory"},
        ),
    )

    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),
        required=False,
        empty_label=_("All categories"),
        widget=forms.HiddenInput(),  # Hidden field for final category selection
    )

    item_type = forms.ChoiceField(
        choices=[("", _("All types")), *Item.ITEM_TYPE_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    sort = forms.ChoiceField(
        choices=[
            ("newest", _("Newest first")),
            ("oldest", _("Oldest first")),
            ("price_low", _("Price: Low to High")),
            ("price_high", _("Price: High to Low")),
            ("name", _("Name A-Z")),
        ],
        required=False,
        initial="newest",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    view = forms.ChoiceField(
        choices=[("grid", _("Grid")), ("list", _("List"))],
        required=False,
        initial="grid",
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up parent category choices
        parent_field = self.fields["parent_category"]
        if isinstance(parent_field, forms.ModelChoiceField):
            parent_field.queryset = ItemCategory.objects.filter(
                parent_category=None,
            )

        # If there's a selected category, set up the hierarchy
        if self.data.get("category"):
            try:
                selected_category = ItemCategory.objects.get(
                    id=self.data.get("category"),
                )

                # Find the root parent
                current = selected_category
                while current.parent_category:
                    current = current.parent_category

                # Set parent category
                if isinstance(parent_field, forms.ModelChoiceField):
                    parent_field.initial = current.pk

                # If selected category has a parent, set up subcategory field
                subcategory_field = self.fields["subcategory"]
                if isinstance(subcategory_field, forms.ModelChoiceField):
                    if selected_category.parent_category:
                        subcategory_field.queryset = ItemCategory.objects.filter(
                            parent_category=selected_category.parent_category,
                        )
                        subcategory_field.initial = selected_category.pk
                    elif current != selected_category:
                        # Selected category is a subcategory of root
                        subcategory_field.queryset = ItemCategory.objects.filter(
                            parent_category=current,
                        )
                        subcategory_field.initial = selected_category.pk
            except ItemCategory.DoesNotExist:
                pass


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["original"]
        widgets = {
            "original": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"},
            ),
        }


class ItemImageUploadForm(forms.Form):
    """Form for uploading images in step 1 of item creation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We'll handle multiple files in the template/JavaScript
        self.fields["images"] = forms.FileField(
            label=_("Upload Images"),
            help_text=_("Select one or more images for your item"),
            required=False,
            widget=forms.FileInput(
                attrs={
                    "accept": "image/*",
                    "class": "form-control",
                    "id": "images-input",
                },
            ),
        )
