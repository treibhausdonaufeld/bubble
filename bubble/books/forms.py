"""
Forms for books app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Book, Author, Genre, Location


class BookFilterForm(forms.Form):
    """Form for filtering books in the list view."""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search books, authors, genres...'),
            'class': 'form-control',
        })
    )
    
    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '5',
        })
    )
    
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '5',
        })
    )
    
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        empty_label=_("All locations"),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    year_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Min year'),
            'min': '1000',
            'max': '2030',
        })
    )
    
    year_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Max year'),
            'min': '1000',
            'max': '2030',
        })
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('newest', _('Newest first')),
            ('oldest', _('Oldest first')),
            ('title', _('Title A-Z')),
            ('year_new', _('Year (newest)')),
            ('year_old', _('Year (oldest)')),
            ('relevance', _('Most relevant')),
        ],
        initial='newest',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )


class BookForm(forms.ModelForm):
    """Form for creating and editing books."""
    
    class Meta:
        model = Book
        fields = [
            'title', 'authors', 'year', 'topic', 'description', 
            'genres', 'location', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter book title'),
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1000',
                'max': '2030',
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Main topic or subject'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Describe the book...'),
            }),
            'authors': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5',
            }),
            'genres': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5',
            }),
            'location': forms.Select(attrs={
                'class': 'form-control',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields except title optional in the form
        for field_name, field in self.fields.items():
            if field_name != 'title':
                field.required = False