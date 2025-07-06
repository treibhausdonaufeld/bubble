from django import forms
from django.utils.translation import gettext_lazy as _

from bubble.categories.models import ItemCategory

from .models import Item

# Constants
MIN_NAME_LENGTH = 3


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


class ItemDetailsForm(forms.ModelForm):
    """Form for editing item details in step 2 of item creation."""

    class Meta:
        model = Item
        fields = [
            "name",
            "description",
            "item_type",
            "price",
            "display_contact",
            "profile_img_frame",
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
                    "placeholder": _("0.00"),
                },
            ),
            "display_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "profile_img_frame": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter categories based on user permissions if needed
        queryset = ItemCategory.objects.all() if user else ItemCategory.objects.none()

        # Update the queryset for the existing field
        self.fields["selected_category"] = forms.ModelChoiceField(
            queryset=queryset,
            required=False,
            widget=forms.HiddenInput(),
            label=_("Selected category"),
        )

        # Make name field optional for step 2 (will be pre-filled from AI)
        self.fields["name"].required = False

        # Set initial category if provided in kwargs
        if "category" in kwargs:
            self.fields["selected_category"].initial = kwargs.pop("category")

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name and len(name.strip()) < MIN_NAME_LENGTH:
            raise forms.ValidationError(
                _("Item name must be at least 3 characters long."),
            )
        return name.strip() if name else name

    def save(self, *, commit=True):
        instance = super().save(commit=False)

        # Set category from selected_category field
        if self.cleaned_data.get("selected_category"):
            instance.category = self.cleaned_data["selected_category"]

        if commit:
            instance.save()
        return instance
