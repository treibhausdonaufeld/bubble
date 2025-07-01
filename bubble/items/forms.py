from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bubble.categories.models import ItemCategory
from bubble.items.models import Image
from bubble.items.models import Item


class ItemForm(forms.ModelForm):
    MIN_ITEM_NAME_LENGTH = 3

    # Category dropdown showing only leaf categories (lowest level)
    selected_category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.filter(
            parent_category__isnull=False,  # Has a parent
            subcategories__isnull=True,  # Has no children
        ),
        required=True,
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
            "item_type",
            "price",
            "display_contact",
            "profile_img_frame",
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
            "item_type": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": _("Price in Euro"),
                },
            ),
            "profile_img_frame": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Profile image frame"),
                },
            ),
            "display_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": _("Item name"),
            "description": _("Description"),
            "item_type": _("Item type"),
            "price": _("Price"),
            "display_contact": _("Show contact"),
            "profile_img_frame": _("Profile image frame"),
            "active": _("Published"),
        }
        help_texts = {
            "display_contact": _("Check to display your contact information"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.root_category = kwargs.pop("root_category", None)
        super().__init__(*args, **kwargs)

        # Show full hierarchy in the dropdown labels
        self.fields["selected_category"].label_from_instance = (
            lambda obj: obj.get_hierarchy()
        )

        # If root_category is provided, filter categories to only show descendants
        if self.root_category:
            descendant_ids = [self.root_category.id]
            descendant_ids.extend(
                [cat.id for cat in self.root_category.get_descendants()],
            )
            self.fields["selected_category"].queryset = ItemCategory.objects.filter(
                id__in=descendant_ids,
                subcategories__isnull=True,  # Only leaf categories
            )

        # If editing an existing item, set the selected category
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

        # Add intern-only fields if user is intern
        if self.user and hasattr(self.user, "profile") and self.user.profile.intern:
            self.fields["intern"] = forms.BooleanField(
                required=False,
                initial=False,
                label=_("Internal"),
                widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                help_text=_("Check if this item is for internal use only"),
            )
            self.fields["th_payment"] = forms.BooleanField(
                required=False,
                initial=False,
                label=_("Treibhaus payment"),
                widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                help_text=_("Accept Treibhaus payment method"),
            )
            # Update Meta.fields to include intern fields
            self.Meta.fields = [*self.Meta.fields, "intern", "th_payment"]

        # Make price required for sell and borrow items
        if hasattr(self, "instance") and self.instance.pk:
            # For existing items, check the item type
            if self.instance.item_type == Item.ITEM_TYPE_FOR_SALE:  # Sell
                self.fields["price"].required = True
                self.fields["price"].label = _("Preis")
            elif self.instance.item_type == Item.ITEM_TYPE_BORROW:  # Borrow
                self.fields["price"].required = False
                self.fields["price"].label = _("Preis pro Woche")
                self.fields["price"].help_text = _(
                    "Leer lassen für kostenloses Verleihen",
                )
            else:  # Give away
                self.fields["price"].required = False
                self.fields["price"].widget = forms.HiddenInput()
        else:
            # For new items, will be handled by JavaScript or default to required
            self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        item_type = self.cleaned_data.get("item_type")

        if (
            item_type == Item.ITEM_TYPE_FOR_SALE and not price
        ):  # Sell item without price
            raise ValidationError(_("Price is required for items for sale."))

        if item_type == Item.ITEM_TYPE_GIVE_AWAY:  # Give away items
            # For give away items, always set price to 0
            return 0.00

        if (
            item_type == Item.ITEM_TYPE_BORROW and not price
        ):  # Borrow item without price
            # For borrow items, empty price means free borrowing
            return 0.00

        return price

    def clean(self):
        cleaned_data = super().clean()
        selected_category = cleaned_data.get("selected_category")

        if not selected_category:
            raise ValidationError(_("Please select a category."))

        # Set the final category
        cleaned_data["category"] = selected_category
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if len(name) < self.MIN_ITEM_NAME_LENGTH:
            raise ValidationError(
                _("Item name must be at least %(min_length)d characters long.")
                % {"min_length": self.MIN_ITEM_NAME_LENGTH},
            )
        return name

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

        # Add required fields
        for field_name, field_config in root_category.required_fields.items():
            self._create_dynamic_field(field_name, field_config, required=True)

        # Add optional fields
        for field_name, field_config in root_category.optional_fields.items():
            self._create_dynamic_field(field_name, field_config, required=False)

    def _create_dynamic_field(self, field_name, field_config, required=False):
        """Create a form field based on configuration"""
        field_type = field_config.get("type", "text")
        label = field_config.get("label", field_name)

        # Get existing value from custom_fields if editing
        initial_value = None
        if self.instance.pk and self.instance.custom_fields:
            initial_value = self.instance.custom_fields.get(field_name)

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
            choices = [(c, c) for c in field_config.get("choices", [])]
            field = forms.ChoiceField(
                label=label,
                required=required,
                choices=choices,
                initial=initial_value,
                widget=forms.Select(attrs={"class": "form-select"}),
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

    def clean(self):
        cleaned_data = super().clean()
        selected_category = cleaned_data.get("selected_category")

        if not selected_category:
            raise ValidationError(_("Please select a category."))

        # Set the final category
        cleaned_data["category"] = selected_category

        # Collect custom field values
        custom_values = {}
        if selected_category:
            root_category = selected_category.get_root_category()
            all_fields = {
                **root_category.required_fields,
                **root_category.optional_fields,
            }

            for field_name in all_fields:
                custom_field_name = f"custom_{field_name}"
                if custom_field_name in cleaned_data:
                    custom_values[field_name] = cleaned_data[custom_field_name]

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

        # Set default values for intern-only fields if user is not intern
        if not (
            self.user and hasattr(self.user, "profile") and self.user.profile.intern
        ):
            instance.intern = False
            instance.th_payment = False

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
        self.fields["parent_category"].queryset = ItemCategory.objects.filter(
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
                self.fields["parent_category"].initial = current.id

                # If selected category has a parent, set up subcategory field
                if selected_category.parent_category:
                    self.fields["subcategory"].queryset = ItemCategory.objects.filter(
                        parent_category=selected_category.parent_category,
                    )
                    self.fields["subcategory"].initial = selected_category.id
                elif current != selected_category:
                    # Selected category is a subcategory of root
                    self.fields["subcategory"].queryset = ItemCategory.objects.filter(
                        parent_category=current,
                    )
                    self.fields["subcategory"].initial = selected_category.id
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
