from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _("Your message..."),
                'required': True
            })
        }
        labels = {
            'message': _("Message")
        }