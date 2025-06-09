from django import forms
from django.core.exceptions import ValidationError
from .models import Item, ItemTagRelation, Image
from willgeben.categories.models import ItemTag, ItemCategory


class ItemForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=ItemTag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select relevant tags for your item"
    )
    
    class Meta:
        model = Item
        fields = [
            'name', 'description', 'category', 'item_type', 'status',
            'price', 'display_contact', 'profile_img_frame', 'active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your item...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'profile_img_frame': forms.TextInput(attrs={'class': 'form-control'}),
            'display_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'active': 'Published',
        }
        help_texts = {
            'display_contact': 'Check to display your contact information',
            'price': 'Leave empty for free items',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Update category choices to show hierarchy
        category_choices = [(cat.id, cat.get_hierarchy()) for cat in ItemCategory.objects.all()]
        self.fields['category'].choices = [('', '---------')] + category_choices
        
        # Add intern-only fields if user is intern
        if self.user and hasattr(self.user, 'profile') and self.user.profile.intern:
            self.fields['intern'] = forms.BooleanField(
                required=False,
                initial=False,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                help_text='Check if this item is for internal use only'
            )
            self.fields['th_payment'] = forms.BooleanField(
                required=False,
                initial=False,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                help_text='Accept Treibhaus payment method'
            )
            # Update Meta.fields to include intern fields
            self.Meta.fields = self.Meta.fields + ['intern', 'th_payment']
        
        # Pre-select existing tags if editing an item
        if self.instance.pk:
            self.fields['tags'].initial = self.instance.tags.values_list('tag_id', flat=True)
        
        # Make price required only for selling items
        self.fields['price'].required = False

    def clean_price(self):
        price = self.cleaned_data.get('price')
        item_type = self.cleaned_data.get('item_type')
        
        if item_type == 0 and not price:  # Sell item without price
            raise ValidationError("Price is required for items being sold.")
        
        if item_type in [1, 2] and price:  # Give away or borrow with price
            raise ValidationError("Price should not be set for items being given away or borrowed.")
        
        return price

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise ValidationError("Item name must be at least 3 characters long.")
        return name

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
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
            'placeholder': 'Search items, tags, categories...'
        })
    )
    
    # Category filters with hierarchy support
    parent_category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.filter(parent_category=None),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select category-filter', 'id': 'parent-category'})
    )
    
    subcategory = forms.ModelChoiceField(
        queryset=ItemCategory.objects.none(),
        required=False,
        empty_label="All Subcategories", 
        widget=forms.Select(attrs={'class': 'form-select category-filter', 'id': 'subcategory'})
    )
    
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.HiddenInput()  # Hidden field for final category selection
    )
    
    item_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Item.ITEM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=ItemTag.objects.all(),
        required=False,
        widget=forms.MultipleHiddenInput()  # Hidden, managed by JavaScript
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Conditions')] + Item.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'), 
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('name', 'Name A-Z'),
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    view = forms.ChoiceField(
        choices=[('grid', 'Grid'), ('list', 'List')],
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