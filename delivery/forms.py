from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import DeliveryPlan, DeliveryStop
from orders.models import Order

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
        
        # Set minimum date (today)
        today = timezone.now().date()
        self.fields['date'].widget.attrs['min'] = today.strftime('%Y-%m-%d')
        
        # Filter driver options to only show drivers
        if self.supplier:
            from users.models import User
            self.fields['driver'].queryset = User.objects.filter(user_type='DRIVER')
            
            # If this is an existing plan, set the supplier
            if not self.instance.pk:
                self.instance.supplier = self.supplier

class DeliveryStopForm(forms.ModelForm):
    """Form for adding stops to a delivery plan"""
    class Meta:
        model = DeliveryStop
        fields = ('order', 'position', 'estimated_arrival_time', 'notes')
        widgets = {
            'estimated_arrival_time': forms.TimeInput(attrs={'type': 'time'}),
            'position': forms.NumberInput(attrs={'min': '1'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.delivery_plan = kwargs.pop('delivery_plan', None)
        super().__init__(*args, **kwargs)
        
        if self.delivery_plan:
            # Filter order options to only show orders from this supplier 
            # that are ready for delivery
            orders_in_plan = self.delivery_plan.stops.values_list('order_id', flat=True)
            self.fields['order'].queryset = Order.objects.filter(
                supplier=self.delivery_plan.supplier,
                status='READY'
            ).exclude(id__in=orders_in_plan)
            
            # Set the next position number
            if not self.instance.pk:
                next_position = self.delivery_plan.stops.count() + 1
                self.fields['position'].initial = next_position
            
            # If this is an existing stop, make order read-only
            if self.instance.pk:
                self.fields['order'].widget.attrs['readonly'] = True

class DeliveryStopStatusForm(forms.Form):
    """Form for updating the status of a delivery stop"""
    STATUS_CHOICES = DeliveryStop.STOP_STATUS_CHOICES
    
    status = forms.ChoiceField(
        label=_('Status'),
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notes = forms.CharField(
        label=_('Notes'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2})
    )
    
    actual_arrival_time = forms.TimeField(
        label=_('Actual Arrival Time'),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    def __init__(self, *args, **kwargs):
        self.stop = kwargs.pop('stop', None)
        super().__init__(*args, **kwargs)
        
        if self.stop:
            # Set initial values
            self.fields['status'].initial = self.stop.status
            self.fields['notes'].initial = self.stop.notes
            self.fields['actual_arrival_time'].initial = self.stop.actual_arrival_time
            
            # Limit available status choices based on current status
            current_status = self.stop.status
            valid_transitions = {
                'PENDING': ['PENDING', 'ARRIVED', 'SKIPPED'],
                'ARRIVED': ['ARRIVED', 'COMPLETED', 'SKIPPED'],
                'COMPLETED': ['COMPLETED'],
                'SKIPPED': ['SKIPPED', 'PENDING'],  # Allow going back to PENDING if skipped by mistake
            }
            
            # Filter choices based on valid transitions
            self.fields['status'].choices = [
                choice for choice in self.STATUS_CHOICES
                if choice[0] in valid_transitions.get(current_status, [])
            ]

class DeliveryPlanFilterForm(forms.Form):
    """Form for filtering delivery plans in list views"""
    COMPLETION_CHOICES = (
        ('', _('All Plans')),
        ('completed', _('Completed')),
        ('active', _('Active')),
    )
    
    completion_status = forms.ChoiceField(
        label=_('Status'),
        choices=COMPLETION_CHOICES,
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
    
    driver = forms.ModelChoiceField(
        label=_('Driver'),
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label=_('All Drivers')
    )
    
    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        # Filter driver options based on supplier
        from users.models import User
        
        if self.supplier:
            # Show only drivers who have delivered for this supplier
            self.fields['driver'].queryset = User.objects.filter(
                user_type='DRIVER',
                delivery_plans__supplier=self.supplier
            ).distinct()
        else:
            # Show all drivers
            self.fields['driver'].queryset = User.objects.filter(user_type='DRIVER')

class StopReorderForm(forms.Form):
    """Form for reordering stops in a delivery plan"""
    # This will be dynamically populated with stop_id_X fields
    
    def __init__(self, *args, **kwargs):
        self.delivery_plan = kwargs.pop('delivery_plan', None)
        super().__init__(*args, **kwargs)
        
        if self.delivery_plan:
            # Add a field for each stop's position
            for stop in self.delivery_plan.stops.all():
                field_name = f'stop_position_{stop.id}'
                self.fields[field_name] = forms.IntegerField(
                    initial=stop.position,
                    min_value=1,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control stop-position',
                        'data-stop-id': stop.id
                    })
                )
