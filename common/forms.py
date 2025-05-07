from django import forms
from django.utils.translation import gettext_lazy as _

class ContactForm(forms.Form):
    """Form for contact/feedback page"""
    name = forms.CharField(
        label=_('Your Name'),
        max_length=100,
        required=True
    )
    
    email = forms.EmailField(
        label=_('Email'),
        required=True
    )
    
    subject = forms.CharField(
        label=_('Subject'),
        max_length=200,
        required=True
    )
    
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={'rows': 5}),
        required=True
    )
    
    user_type = forms.ChoiceField(
        label=_('I am a'),
        choices=(
            ('SUPPLIER', _('Supplier')),
            ('SHOP', _('Shop/Retailer')),
            ('OTHER', _('Other')),
        ),
        required=True
    )

class SearchForm(forms.Form):
    """Generic search form for global search functionality"""
    query = forms.CharField(
        label='',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search...'),
            'class': 'form-control search-input'
        })
    )
    
    search_type = forms.ChoiceField(
        label=_('Search In'),
        choices=(
            ('ALL', _('All')),
            ('PRODUCTS', _('Products')),
            ('SUPPLIERS', _('Suppliers')),
            ('SHOPS', _('Shops')),
            ('ORDERS', _('Orders')),
        ),
        required=False,
        initial='ALL'
    )
