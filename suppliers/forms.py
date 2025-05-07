from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Supplier
from products.models import Product, Category
from delivery.models import DeliveryPlan

class SupplierForm(forms.ModelForm):
    """Form for creating and editing supplier information"""
    class Meta:
        model = Supplier
        fields = ('name', 'description', 'address', 'city', 'country', 'tax_id', 'email', 'phone', 'logo')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

class ProductForm(forms.ModelForm):
    """Form for creating and editing products"""
    class Meta:
        model = Product
        fields = ('name', 'description', 'sku', 'barcode', 'unit', 'price', 
                  'image', 'is_available', 'min_order_quantity', 'category')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'min_order_quantity': forms.NumberInput(attrs={'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        if self.supplier:
            # Filter categories to only show ones belonging to this supplier
            self.fields['category'].queryset = Category.objects.filter(supplier=self.supplier)

class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    class Meta:
        model = Category
        fields = ('name', 'description', 'parent')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        if self.supplier:
            # Filter parent category options to only show ones belonging to this supplier
            self.fields['parent'].queryset = Category.objects.filter(supplier=self.supplier)

class ProductImportForm(forms.Form):
    """Form for importing products from a CSV file"""
    csv_file = forms.FileField(
        label=_('CSV File'),
        help_text=_('Please upload a CSV file with the following columns: name, description, sku, barcode, unit, price, category')
    )
    
    create_missing_categories = forms.BooleanField(
        label=_('Create missing categories'),
        help_text=_('If checked, missing categories will be automatically created'),
        required=False,
        initial=True
    )

class DeliveryPlanForm(forms.ModelForm):
    """Form for creating and editing delivery plans"""
    class Meta:
        model = DeliveryPlan
        fields = ('date', 'driver', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        if self.supplier:
            # Filter driver options to only show ones with DRIVER user_type
            from users.models import User
            self.fields['driver'].queryset = User.objects.filter(user_type='DRIVER')

class OrderFilterForm(forms.Form):
    """Form for filtering orders"""
    STATUS_CHOICES = (
        ('', _('All Statuses')),
        ('DRAFT', _('Draft')),
        ('SUBMITTED', _('Submitted')),
        ('CONFIRMED', _('Confirmed')),
        ('PROCESSING', _('Processing')),
        ('READY', _('Ready for Delivery')),
        ('DELIVERING', _('Out for Delivery')),
        ('DELIVERED', _('Delivered')),
        ('CANCELLED', _('Cancelled')),
    )
    
    status = forms.ChoiceField(
        label=_('Status'),
        choices=STATUS_CHOICES,
        required=False
    )
    
    shop = forms.ModelChoiceField(
        label=_('Shop'),
        queryset=None,
        required=False,
        empty_label=_('All Shops')
    )
    
    date_from = forms.DateField(
        label=_('From Date'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    date_to = forms.DateField(
        label=_('To Date'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        if self.supplier:
            # Filter shop options to only show ones that have ordered from this supplier
            from shops.models import Shop
            self.fields['shop'].queryset = Shop.objects.filter(orders__supplier=self.supplier).distinct()
