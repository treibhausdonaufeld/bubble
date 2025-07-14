from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bubble.items.models import Image, Item, ItemCategory


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
            "status",
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
            "status": forms.Select(attrs={"class": "form-select select2-field"}),
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
            "status": _("Condition"),
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

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}

        selected_category = cleaned_data.get("selected_category")

        # Set the final category
        cleaned_data["category"] = selected_category

        return cleaned_data

    def save(self, *, commit: bool = True):
        instance = super().save(commit=False)

        if self.user:
            instance.user = self.user

        # Set the category from cascading dropdowns
        category = self.cleaned_data.get("category")
        if category:
            instance.category = category

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

    status = forms.ChoiceField(
        choices=[("", _("All conditions")), *Item.STATUS_CHOICES],
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
