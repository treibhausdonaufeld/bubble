from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Favorite, FavoriteList

User = get_user_model()


class FavoriteListForm(forms.ModelForm):
    """Form for creating and editing favorite lists."""

    class Meta:
        model = FavoriteList
        fields = ["name", "shared_with", "editors"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "shared_with": forms.SelectMultiple(
                attrs={"class": "form-select select2-users", "multiple": "multiple"}
            ),
            "editors": forms.SelectMultiple(
                attrs={"class": "form-select select2-users", "multiple": "multiple"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter out the current user from shared_with and editors
        if self.user:
            self.fields["shared_with"].queryset = User.objects.exclude(pk=self.user.pk)
            self.fields["editors"].queryset = User.objects.exclude(pk=self.user.pk)

        # Add Bootstrap classes and placeholders
        self.fields["name"].widget.attrs.update(
            {
                "placeholder": _("Enter list name"),
                "class": "form-control",
            }
        )

        # Override label_from_instance to display users as "username (Full Name)"
        def user_label(user):
            if user.name:
                return f"{user.username} ({user.name})"
            return user.username

        self.fields["shared_with"].label_from_instance = user_label
        self.fields["editors"].label_from_instance = user_label


class FavoriteWithListForm(forms.ModelForm):
    """Form for creating favorites with list selection."""

    class Meta:
        model = Favorite
        fields = ["title", "url", "favorite_list"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.URLInput(attrs={"class": "form-control"}),
            "favorite_list": forms.Select(attrs={"class": "form-select"}),
        }


class ManualFavoriteForm(forms.Form):
    """Form for manually creating favorites with multiple list selection."""

    title = forms.CharField(
        max_length=255,
        label=_("Title"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    url = forms.URLField(
        label=_("URL"),
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )
    favorite_lists = forms.ModelMultipleChoiceField(
        queryset=FavoriteList.objects.none(),
        label=_("Add to Lists"),
        widget=forms.SelectMultiple(
            attrs={"class": "form-select select2-lists", "multiple": "multiple"}
        ),
        required=True,
        help_text=_("Select one or more lists to add this favorite to"),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter favorite lists to only show user's accessible lists
        if self.user:
            self.fields[
                "favorite_lists"
            ].queryset = FavoriteList.get_user_accessible_lists(self.user)

            # Set default to user's default list if it exists
            try:
                default_list = FavoriteList.objects.get(user=self.user, is_default=True)
                self.fields["favorite_lists"].initial = [default_list]
            except FavoriteList.DoesNotExist:
                pass

        # Add Bootstrap classes and placeholders
        self.fields["title"].widget.attrs.update(
            {
                "placeholder": _("Enter favorite title"),
                "class": "form-control",
            }
        )
        self.fields["url"].widget.attrs.update(
            {
                "placeholder": _("Enter URL (e.g., https://example.com)"),
                "class": "form-control",
            }
        )


class ShareFavoriteListForm(forms.Form):
    """Form for sharing favorite lists with other users."""

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(
            attrs={"class": "form-select select2-users", "multiple": "multiple"}
        ),
        label=_("Share with users"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter out the current user
        if self.user:
            self.fields["users"].queryset = User.objects.exclude(pk=self.user.pk)

        # Override label_from_instance to display users as "username (Full Name)"
        def user_label(user):
            if user.name:
                return f"{user.username} ({user.name})"
            return user.username

        self.fields["users"].label_from_instance = user_label


class ManageFavoriteForm(forms.Form):
    """Form for managing existing favorites (add/remove from lists)."""

    title = forms.CharField(
        max_length=255,
        label=_("Title"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    url = forms.URLField(
        label=_("URL"),
        widget=forms.URLInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )
    favorite_lists = forms.ModelMultipleChoiceField(
        queryset=FavoriteList.objects.none(),
        label=_("In Lists"),
        widget=forms.SelectMultiple(
            attrs={"class": "form-select select2-lists", "multiple": "multiple"}
        ),
        required=False,
        help_text=_(
            "Select lists to save this favorite to. "
            "Remove from lists by deselecting them."
        ),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.url = kwargs.pop("url", None)
        super().__init__(*args, **kwargs)

        # Filter favorite lists to only show user's accessible lists
        if self.user:
            self.fields[
                "favorite_lists"
            ].queryset = FavoriteList.get_user_accessible_lists(self.user)

            # If URL provided, set initial values from existing favorites
            if self.url:
                existing_favorites = Favorite.objects.filter(
                    user=self.user, url=self.url
                )
                if existing_favorites.exists():
                    # Use title from first favorite
                    self.fields["title"].initial = existing_favorites.first().title
                    # Set initial lists (all lists this URL is currently in)
                    current_lists = [fav.favorite_list for fav in existing_favorites]
                    self.fields["favorite_lists"].initial = current_lists

                # Set the URL
                self.fields["url"].initial = self.url

        # Add Bootstrap classes and placeholders
        self.fields["title"].widget.attrs.update(
            {
                "placeholder": _("Enter favorite title"),
                "class": "form-control",
            }
        )
        self.fields["url"].widget.attrs.update(
            {
                "class": "form-control",
            }
        )
