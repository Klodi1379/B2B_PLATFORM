from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Product, Category

class ProductSearchForm(forms.Form):
    """Form for searching products"""
    query = forms.CharField(
        label=_('Search'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Search products...')})
    )
    
    category = forms.ModelChoiceField(
        label=_('Category'),
        queryset=Category.objects.all(),
        required=False,
        empty_label=_('All Categories')
    )
    
    supplier = forms.ModelChoiceField(
        label=_('Supplier'),
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label=_('All Suppliers')
    )
    
    min_price = forms.DecimalField(
        label=_('Min Price'),
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
    )
    
    max_price = forms.DecimalField(
        label=_('Max Price'),
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
    )
    
    available_only = forms.BooleanField(
        label=_('Available Products Only'),
        required=False,
        initial=True
    )
    
    def __init__(self, *args, **kwargs):
        from suppliers.models import Supplier
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        
        # Optional filtering of categories by supplier
        supplier_id = kwargs.get('data', {}).get('supplier')
        if supplier_id:
            self.fields['category'].queryset = Category.objects.filter(supplier_id=supplier_id)

class CategoryFilterForm(forms.Form):
    """Form for filtering categories"""
    supplier = forms.ModelChoiceField(
        label=_('Supplier'),
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label=_('All Suppliers')
    )
    
    parent = forms.ModelChoiceField(
        label=_('Parent Category'),
        queryset=Category.objects.filter(parent__isnull=True),
        required=False,
        empty_label=_('All Parent Categories')
    )
    
    def __init__(self, *args, **kwargs):
        from suppliers.models import Supplier
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        
        # Optional filtering of parent categories by supplier
        supplier_id = kwargs.get('data', {}).get('supplier')
        if supplier_id:
            self.fields['parent'].queryset = Category.objects.filter(
                supplier_id=supplier_id,
                parent__isnull=True
            )

class ProductForm(forms.ModelForm):
    """Form for creating and editing products (for admin use)"""
    class Meta:
        model = Product
        fields = ('name', 'description', 'supplier', 'category', 'sku', 'barcode',
                 'unit', 'price', 'image', 'is_available', 'min_order_quantity')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'min_order_quantity': forms.NumberInput(attrs={'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If this is an existing product, filter categories by supplier
        if self.instance and self.instance.pk and self.instance.supplier:
            self.fields['category'].queryset = Category.objects.filter(supplier=self.instance.supplier)
        
        # We need to link the category field to supplier changes
        self.fields['supplier'].widget.attrs['onchange'] = 'updateCategoryOptions(this.value)'

class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories (for admin use)"""
    class Meta:
        model = Category
        fields = ('name', 'description', 'supplier', 'parent')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If this is an existing category, filter parent options by supplier
        if self.instance and self.instance.pk and self.instance.supplier:
            self.fields['parent'].queryset = Category.objects.filter(
                supplier=self.instance.supplier
            ).exclude(pk=self.instance.pk)  # Exclude self to prevent circular references
        
        # We need to link the parent field to supplier changes
        self.fields['supplier'].widget.attrs['onchange'] = 'updateParentOptions(this.value)'
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        supplier = cleaned_data.get('supplier')
        
        # Ensure parent category belongs to the same supplier
        if parent and supplier and parent.supplier != supplier:
            self.add_error(
                'parent',
                _('Parent category must belong to the same supplier')
            )
        
        return cleaned_data
