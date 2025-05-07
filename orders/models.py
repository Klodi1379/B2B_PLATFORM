from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Order(models.Model):
    """Customer order"""
    ORDER_STATUS_CHOICES = (
        ('DRAFT', _('Draft')),
        ('SUBMITTED', _('Submitted')),
        ('CONFIRMED', _('Confirmed')),
        ('PROCESSING', _('Processing')),
        ('READY', _('Ready for Delivery')),
        ('DELIVERING', _('Out for Delivery')),
        ('DELIVERED', _('Delivered')),
        ('CANCELLED', _('Cancelled')),
    )
    
    shop = models.ForeignKey(
        'shops.Shop', 
        on_delete=models.PROTECT, 
        related_name='orders',
        verbose_name=_('Shop')
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier', 
        on_delete=models.PROTECT, 
        related_name='orders',
        verbose_name=_('Supplier')
    )
    status = models.CharField(
        _('Status'), 
        max_length=20, 
        choices=ORDER_STATUS_CHOICES, 
        default='DRAFT'
    )
    notes = models.TextField(_('Notes'), blank=True)
    total_amount = models.DecimalField(_('Total Amount'), max_digits=10, decimal_places=2, default=0)
    
    # Delivery information
    delivery_date = models.DateField(_('Delivery Date'), null=True, blank=True)
    delivery_time_window = models.CharField(_('Delivery Time Window'), max_length=50, blank=True)  # e.g., "Morning", "14:00-16:00"
    
    # Timestamps and metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    submitted_at = models.DateTimeField(_('Submitted At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.shop.name} from {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount before saving
        if self.id:  # Only for existing orders
            self.total_amount = sum(item.total_price for item in self.items.all())
            
        # Set submitted_at timestamp when status changes to SUBMITTED
        if self.status == 'SUBMITTED' and not self.submitted_at:
            self.submitted_at = timezone.now()
            
        super().save(*args, **kwargs)
        
    def get_status_display_class(self):
        """Return CSS class based on status for UI styling"""
        status_classes = {
            'DRAFT': 'secondary',
            'SUBMITTED': 'info',
            'CONFIRMED': 'primary',
            'PROCESSING': 'primary',
            'READY': 'success',
            'DELIVERING': 'warning',
            'DELIVERED': 'success',
            'CANCELLED': 'danger'
        }
        return status_classes.get(self.status, 'secondary')
        
    def can_be_cancelled(self):
        """Check if order can be cancelled based on its status"""
        return self.status in ['DRAFT', 'SUBMITTED', 'CONFIRMED']
        
    def can_be_edited(self):
        """Check if order can be edited"""
        return self.status == 'DRAFT'

class OrderItem(models.Model):
    """Individual item in an order"""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name=_('Order')
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.PROTECT,
        verbose_name=_('Product')
    )
    quantity = models.DecimalField(_('Quantity'), max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(_('Unit Price'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('Total Price'), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update order total
        self.order.save()
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
