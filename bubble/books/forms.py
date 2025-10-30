"""
Forms for books app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Book, Location


class BookFilterForm(forms.Form):
    """Form for filtering books in the list view."""

    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Search books, authors, genres..."),
                "class": "form-control",
            }
        ),
    )

    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        empty_label=_("All locations"),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    year_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Min year"),
                "min": "1000",
                "max": "2030",
            }
        ),
    )

    year_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Max year"),
                "min": "1000",
                "max": "2030",
            }
        ),
    )

    sort = forms.ChoiceField(
        choices=[
            ("newest", _("Newest first")),
            ("oldest", _("Oldest first")),
            ("title", _("Title A-Z")),
            ("year_new", _("Year (newest)")),
            ("year_old", _("Year (oldest)")),
            ("relevance", _("Most relevant")),
        ],
        initial="newest",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )


class BookForm(forms.ModelForm):
    """Form for creating and editing books."""

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "authors",
            "year",
            "publisher",
            "place",
            "topics",
            "description",
            "genres",
            "language",
            "page_count",
            "location",
            "ownership",
            "abbreviation",
            "regal",
            "booked",
            "booked_till",
            "image",
        ]
        widgets = {
            "isbn": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("ISBN number (ISBN-10 or ISBN-13)"),
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter book title"),
                }
            ),
            "authors": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Author names (comma-separated)"),
                }
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1000",
                    "max": "2030",
                }
            ),
            "publisher": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Publisher name"),
                }
            ),
            "place": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Place of publication"),
                }
            ),
            "topics": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Book topics (comma-separated)"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Describe the book..."),
                }
            ),
            "genres": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Book genres (comma-separated)"),
                }
            ),
            "language": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Language code (e.g., de, en, cs)"),
                    "maxlength": "10",
                }
            ),
            "page_count": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Number of pages"),
                }
            ),
            "location": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "ownership": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "abbreviation": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Library abbreviation"),
                }
            ),
            "regal": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "booked": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "booked_till": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields except title optional in the form
        for field_name, field in self.fields.items():
            if field_name != "title":
                field.required = False

    def clean(self):
        cleaned_data = super().clean()
        ownership = cleaned_data.get("ownership")
        abbreviation = cleaned_data.get("abbreviation")
        booked = cleaned_data.get("booked")
        booked_till = cleaned_data.get("booked_till")

        # Validate abbreviation is provided when ownership is library
        if ownership == "library" and not abbreviation:
            self.add_error(
                "abbreviation", _("Abbreviation is required when ownership is library")
            )

        # Validate booked_till is provided when booked is True
        if booked and not booked_till:
            self.add_error(
                "booked_till", _("Booked till date is required when book is booked")
            )

        # Clear booked_till if booked is False
        if not booked and booked_till:
            cleaned_data["booked_till"] = None

        return cleaned_data
