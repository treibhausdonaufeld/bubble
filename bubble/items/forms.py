from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Item, ItemTagRelation, Image
from bubble.categories.models import ItemCategory
from bubble.tags.models import ItemTag


class ItemForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=ItemTag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Tags"),
        help_text=_("Select relevant tags for your item")
    )
    
    # Dynamic cascading category dropdown
    # Only one field needed - will be populated dynamically with JavaScript
    selected_category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),
        required=True,
        widget=forms.HiddenInput(),
        label=_("Selected category")
    )

    class Meta:
        model = Item
        fields = [
            'name', 'description', 'item_type', 'status',
            'price', 'display_contact', 'profile_img_frame', 'active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Item name')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Describe your item...')}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': _('Price in Euro')}),
            'profile_img_frame': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Profile image frame')}),
            'display_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': _("Item name"),
            'description': _("Description"),
            'item_type': _("Item type"),
            'status': _("Condition"),
            'price': _("Price"),
            'display_contact': _("Show contact"),
            'profile_img_frame': _("Profile image frame"),
            'active': _("Published"),
        }
        help_texts = {
            'display_contact': _("Check to display your contact information"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If editing an existing item, set the selected category
        if self.instance.pk and hasattr(self.instance, 'category') and self.instance.category:
            self.fields['selected_category'].initial = self.instance.category

        # Add intern-only fields if user is intern
        if self.user and hasattr(self.user, 'profile') and self.user.profile.intern:
            self.fields['intern'] = forms.BooleanField(
                required=False,
                initial=False,
                label=_("Internal"),
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                help_text=_("Check if this item is for internal use only")
            )
            self.fields['th_payment'] = forms.BooleanField(
                required=False,
                initial=False,
                label=_("Treibhaus payment"),
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                help_text=_("Accept Treibhaus payment method")
            )
            # Update Meta.fields to include intern fields
            self.Meta.fields = self.Meta.fields + ['intern', 'th_payment']

        # Pre-select existing tags if editing an item
        if self.instance.pk:
            self.fields['tags'].initial = self.instance.tags.values_list('tag_id', flat=True)

        # Make price required for sell and borrow items
        if hasattr(self, 'instance') and self.instance.pk:
            # For existing items, check the item type
            if self.instance.item_type == 0:  # Sell
                self.fields['price'].required = True
                self.fields['price'].label = _("Preis")
            elif self.instance.item_type == 2:  # Borrow
                self.fields['price'].required = False
                self.fields['price'].label = _("Preis pro Woche")
                self.fields['price'].help_text = _("Leer lassen für kostenloses Verleihen")
            else:  # Give away
                self.fields['price'].required = False
                self.fields['price'].widget = forms.HiddenInput()
        else:
            # For new items, will be handled by JavaScript or default to required
            self.fields['price'].required = False

    def clean_price(self):
        price = self.cleaned_data.get('price')
        item_type = self.cleaned_data.get('item_type')

        if item_type == 0 and not price:  # Sell item without price
            raise ValidationError(_("Preis ist erforderlich für Verkaufsartikel."))

        if item_type == 1:  # Give away items
            if not price:
                raise ValidationError(_("Wenn der Artikel kostenlos ist, wählen Sie den Typ 'Verschenken'."))
            # For give away items, always set price to 0
            return 0.00

        if item_type == 2 and not price:  # Borrow item without price
            # For borrow items, empty price means free borrowing
            return 0.00
            
        return price

    def clean(self):
        cleaned_data = super().clean()
        selected_category = cleaned_data.get('selected_category')
        
        if not selected_category:
            raise ValidationError(_("Please select a category."))
            
        # Set the final category
        cleaned_data['category'] = selected_category
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise ValidationError(_("Item name must be at least 3 characters long."))
        return name

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            instance.user = self.user

        # Set the category from cascading dropdowns
        category = self.cleaned_data.get('category')
        if category:
            instance.category = category

        # Set default values for intern-only fields if user is not intern
        if not (self.user and hasattr(self.user, 'profile') and self.user.profile.intern):
            instance.intern = False
            instance.th_payment = False

        if commit:
            instance.save()
            self.save_tags(instance)

        return instance

    def save_tags(self, instance):
        # Clear existing tag relationships
        ItemTagRelation.objects.filter(item=instance).delete()

        # Create new tag relationships
        selected_tags = self.cleaned_data.get('tags', [])
        for tag in selected_tags:
            ItemTagRelation.objects.create(item=instance, tag=tag)


class ItemFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': _("Search items, tags, categories...")
        })
    )

    # Category filters with hierarchy support
    parent_category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.filter(parent_category=None),
        required=False,
        empty_label=_("All categories"),
        widget=forms.Select(attrs={'class': 'form-select category-filter', 'id': 'parent-category'})
    )

    subcategory = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        empty_label=_("All subcategories"),
        widget=forms.Select(attrs={'class': 'form-select category-filter', 'id': 'subcategory'})
    )

    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),
        required=False,
        empty_label=_("All categories"),
        widget=forms.HiddenInput()  # Hidden field for final category selection
    )

    item_type = forms.ChoiceField(
        choices=[('', _("All types"))] + Item.ITEM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=ItemTag.objects.all(),
        required=False,
        widget=forms.MultipleHiddenInput()  # Hidden, managed by JavaScript
    )

    status = forms.ChoiceField(
        choices=[('', _("All conditions"))] + Item.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sort = forms.ChoiceField(
        choices=[
            ('newest', _("Newest first")),
            ('oldest', _("Oldest first")),
            ('price_low', _("Price: Low to High")),
            ('price_high', _("Price: High to Low")),
            ('name', _("Name A-Z")),
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    view = forms.ChoiceField(
        choices=[('grid', _("Grid")), ('list', _("List"))],
        required=False,
        initial='grid',
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up parent category choices
        self.fields['parent_category'].queryset = ItemCategory.objects.filter(parent_category=None)

        # If there's a selected category, set up the hierarchy
        if self.data.get('category'):
            try:
                selected_category = ItemCategory.objects.get(id=self.data.get('category'))

                # Find the root parent
                current = selected_category
                while current.parent_category:
                    current = current.parent_category

                # Set parent category
                self.fields['parent_category'].initial = current.id

                # If selected category has a parent, set up subcategory field
                if selected_category.parent_category:
                    self.fields['subcategory'].queryset = ItemCategory.objects.filter(
                        parent_category=selected_category.parent_category
                    )
                    self.fields['subcategory'].initial = selected_category.id
                elif current != selected_category:
                    # Selected category is a subcategory of root
                    self.fields['subcategory'].queryset = ItemCategory.objects.filter(
                        parent_category=current
                    )
                    self.fields['subcategory'].initial = selected_category.id
            except ItemCategory.DoesNotExist:
                pass


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['fname']
        widgets = {
            'fname': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }