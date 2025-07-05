from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ItemTag


class TagForm(forms.ModelForm):
    class Meta:
        model = ItemTag
        fields = ["name", "description"]
        labels = {
            "name": _("Name"),
            "description": _("Description"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
