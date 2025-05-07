from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Shop
from orders.models import Order, OrderItem
from suppliers.models import Supplier

class ShopForm(forms.ModelForm):
    """Form for creating and editing shop information"""
    class Meta:
        model = Shop
        fields = ('name', 'shop_type', 'address', 'city', 'country',
                 'latitude', 'longitude', 'tax_id', 'email', 'phone')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'latitude': forms.NumberInput(attrs={'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'step': 'any'}),
        }

class OrderForm(forms.ModelForm):
    """Form for creating and editing orders"""
    class Meta:
        model = Order
        fields = ('supplier', 'notes', 'delivery_date', 'delivery_time_window')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'supplier': forms.HiddenInput(),  # Hide supplier field as it's set automatically
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Delivery date should be at least tomorrow
        import datetime
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self.fields['delivery_date'].widget.attrs['min'] = tomorrow.strftime('%Y-%m-%d')

        # Add required attribute to delivery_date field
        self.fields['delivery_date'].required = True

        if self.user and self.user.is_shop:
            try:
                shop = Shop.objects.get(admin=self.user)
                
                # Get all suppliers that this shop has ordered from before
                suppliers = Supplier.objects.filter(orders__shop=shop).distinct()

                # If there are no previous suppliers, show all active suppliers
                if not suppliers.exists():
                    suppliers = Supplier.objects.filter(is_active=True)

                self.fields['supplier'].queryset = suppliers
            except Shop.DoesNotExist:
                # If shop doesn't exist, just show all active suppliers
                self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)

class OrderItemForm(forms.ModelForm):
    """Form for adding items to an order"""
    class Meta:
        model = OrderItem
        fields = ('product', 'quantity')
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1', 'step': 'any'}),
        }

    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)

        if self.supplier:
            # Filter products to only show ones belonging to this supplier
            from products.models import Product
            self.fields['product'].queryset = Product.objects.filter(
                supplier=self.supplier,
                is_available=True
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')

        if quantity < product.min_order_quantity:
            raise forms.ValidationError(
                _('Minimum order quantity for this product is %(min_qty)s'),
                params={'min_qty': product.min_order_quantity}
            )

        return quantity

class SupplierSearchForm(forms.Form):
    """Form for searching suppliers"""
    name = forms.CharField(
        label=_('Supplier Name'),
        required=False
    )

    city = forms.CharField(
        label=_('City'),
        required=False
    )

    category = forms.CharField(
        label=_('Product Category'),
        required=False,
        help_text=_('Search suppliers by product category')
    )

class CartAddProductForm(forms.Form):
    """Form for adding a product to the cart"""
    quantity = forms.DecimalField(
        label=_('Quantity'),
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': 'any', 'min': '0.01'})
    )

    update = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if self.product:
            self.fields['quantity'].min_value = self.product.min_order_quantity
            self.fields['quantity'].widget.attrs['min'] = self.product.min_order_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')

        if self.product and quantity < self.product.min_order_quantity:
            raise forms.ValidationError(
                _('Minimum order quantity for this product is %(min_qty)s'),
                params={'min_qty': self.product.min_order_quantity}
            )

        return quantity
