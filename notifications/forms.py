from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Notification

class NotificationFilterForm(forms.Form):
    """Form for filtering notifications in list views"""
    TYPE_CHOICES = (
        ('', _('All Types')),
    ) + Notification.NOTIFICATION_TYPE_CHOICES
    
    READ_CHOICES = (
        ('', _('All Notifications')),
        ('read', _('Read Only')),
        ('unread', _('Unread Only')),
    )
    
    type = forms.ChoiceField(
        label=_('Type'),
        choices=TYPE_CHOICES,
        required=False
    )
    
    read_status = forms.ChoiceField(
        label=_('Read Status'),
        choices=READ_CHOICES,
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

class NotificationForm(forms.ModelForm):
    """Form for creating notifications (admin/system use)"""
    class Meta:
        model = Notification
        fields = ('recipient', 'type', 'title', 'message', 'order', 'delivery_plan')
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Recipients are filtered in the view based on the type of notification
        # and the related objects (order, delivery_plan)
        
        # Make optional fields not required
        self.fields['order'].required = False
        self.fields['delivery_plan'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        notification_type = cleaned_data.get('type')
        order = cleaned_data.get('order')
        delivery_plan = cleaned_data.get('delivery_plan')
        
        # Validate that appropriate related objects are provided based on type
        if notification_type == 'ORDER_STATUS' and not order:
            self.add_error('order', _('Order is required for order status notifications'))
        
        if notification_type == 'DELIVERY_UPDATE' and not delivery_plan:
            self.add_error('delivery_plan', _('Delivery plan is required for delivery update notifications'))
        
        return cleaned_data

class BulkNotificationForm(forms.Form):
    """Form for creating notifications for multiple recipients"""
    TYPE_CHOICES = Notification.NOTIFICATION_TYPE_CHOICES
    
    type = forms.ChoiceField(
        label=_('Type'),
        choices=TYPE_CHOICES
    )
    
    title = forms.CharField(
        label=_('Title'),
        max_length=100
    )
    
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={'rows': 3})
    )
    
    recipient_groups = forms.MultipleChoiceField(
        label=_('Recipient Groups'),
        choices=(
            ('SUPPLIER', _('All Suppliers')),
            ('SHOP', _('All Shops')),
            ('DRIVER', _('All Drivers')),
            ('ADMIN', _('All Administrators')),
        ),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
