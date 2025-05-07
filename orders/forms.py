from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Order, OrderItem

class OrderForm(forms.ModelForm):
    """Form for creating and editing orders"""
    class Meta:
        model = Order
        fields = ('shop', 'supplier', 'notes', 'delivery_date', 'delivery_time_window')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum date for delivery (tomorrow)
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        self.fields['delivery_date'].widget.attrs['min'] = tomorrow.strftime('%Y-%m-%d')
        
        # Filter shop and supplier based on user type
        if self.user:
            from shops.models import Shop
            from suppliers.models import Supplier
            
            if self.user.is_shop:
                # Shop users can only create orders for their shop
                shop = Shop.objects.filter(admin=self.user).first()
                if shop:
                    self.fields['shop'].initial = shop
                    self.fields['shop'].widget = forms.HiddenInput()
                    
                    # Show only suppliers that the shop has ordered from before
                    suppliers = Supplier.objects.filter(orders__shop=shop).distinct()
                    if not suppliers.exists():
                        # If no previous orders, show all active suppliers
                        suppliers = Supplier.objects.filter(is_active=True)
                    
                    self.fields['supplier'].queryset = suppliers
            
            elif self.user.is_supplier:
                # Supplier users can only create orders for their supplier
                supplier = Supplier.objects.filter(admin=self.user).first()
                if supplier:
                    self.fields['supplier'].initial = supplier
                    self.fields['supplier'].widget = forms.HiddenInput()
                    
                    # Show only shops that have ordered from this supplier before
                    shops = Shop.objects.filter(orders__supplier=supplier).distinct()
                    if not shops.exists():
                        # If no previous orders, show all active shops
                        shops = Shop.objects.filter(is_active=True)
                    
                    self.fields['shop'].queryset = shops

class OrderItemForm(forms.ModelForm):
    """Form for adding items to an order"""
    class Meta:
        model = OrderItem
        fields = ('product', 'quantity', 'unit_price')
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '0.01', 'step': 'any'}),
            'unit_price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order and self.order.supplier:
            # Filter products to only show ones from this supplier
            from products.models import Product
            self.fields['product'].queryset = Product.objects.filter(
                supplier=self.order.supplier,
                is_available=True
            )
            
            # If product is selected, set initial unit price
            if 'product' in self.data:
                try:
                    product_id = int(self.data.get('product'))
                    product = Product.objects.get(id=product_id)
                    self.fields['unit_price'].initial = product.price
                except (ValueError, Product.DoesNotExist):
                    pass
        
        # If this is an existing order item, make product read-only
        if self.instance and self.instance.pk:
            self.fields['product'].widget.attrs['readonly'] = True
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')
        
        if product and quantity < product.min_order_quantity:
            raise forms.ValidationError(
                _('Minimum order quantity for this product is %(min_qty)s'),
                params={'min_qty': product.min_order_quantity}
            )
        
        return quantity

class OrderStatusForm(forms.Form):
    """Form for updating order status"""
    STATUS_CHOICES = Order.ORDER_STATUS_CHOICES
    
    status = forms.ChoiceField(
        label=_('Status'),
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Set initial status
            self.fields['status'].initial = self.order.status
            
            # Limit available status choices based on current status
            current_status = self.order.status
            valid_transitions = {
                'DRAFT': ['DRAFT', 'SUBMITTED', 'CANCELLED'],
                'SUBMITTED': ['SUBMITTED', 'CONFIRMED', 'CANCELLED'],
                'CONFIRMED': ['CONFIRMED', 'PROCESSING', 'CANCELLED'],
                'PROCESSING': ['PROCESSING', 'READY', 'CANCELLED'],
                'READY': ['READY', 'DELIVERING', 'CANCELLED'],
                'DELIVERING': ['DELIVERING', 'DELIVERED', 'CANCELLED'],
                'DELIVERED': ['DELIVERED'],
                'CANCELLED': ['CANCELLED'],
            }
            
            # Filter choices based on valid transitions
            self.fields['status'].choices = [
                choice for choice in self.STATUS_CHOICES
                if choice[0] in valid_transitions.get(current_status, [])
            ]

class OrderFilterForm(forms.Form):
    """Form for filtering orders in list views"""
    STATUS_CHOICES = (
        ('', _('All Statuses')),
    ) + Order.ORDER_STATUS_CHOICES
    
    status = forms.ChoiceField(
        label=_('Status'),
        choices=STATUS_CHOICES,
        required=False
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
    
    # These fields will be conditionally added based on user type
    shop = None
    supplier = None
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add shop/supplier filter based on user type
        if self.user:
            from shops.models import Shop
            from suppliers.models import Supplier
            
            if self.user.is_supplier:
                # Supplier users need to filter by shop
                self.fields['shop'] = forms.ModelChoiceField(
                    label=_('Shop'),
                    queryset=Shop.objects.filter(
                        orders__supplier__admin=self.user
                    ).distinct(),
                    required=False,
                    empty_label=_('All Shops')
                )
            
            elif self.user.is_shop:
                # Shop users need to filter by supplier
                self.fields['supplier'] = forms.ModelChoiceField(
                    label=_('Supplier'),
                    queryset=Supplier.objects.filter(
                        orders__shop__admin=self.user
                    ).distinct(),
                    required=False,
                    empty_label=_('All Suppliers')
                )
