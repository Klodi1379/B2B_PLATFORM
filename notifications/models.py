from django.db import models
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """System notification for users"""
    NOTIFICATION_TYPE_CHOICES = (
        ('ORDER_STATUS', _('Order Status Change')),
        ('NEW_ORDER', _('New Order')),
        ('DELIVERY_UPDATE', _('Delivery Update')),
        ('SYSTEM', _('System Notification')),
    )
    
    recipient = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name=_('Recipient')
    )
    type = models.CharField(_('Type'), max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(_('Title'), max_length=100)
    message = models.TextField(_('Message'))
    is_read = models.BooleanField(_('Read'), default=False)
    
    # Optional relation to relevant objects
    order = models.ForeignKey(
        'orders.Order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('Order')
    )
    delivery_plan = models.ForeignKey(
        'delivery.DeliveryPlan', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('Delivery Plan')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type} - {self.title}"
        
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()
        
    def get_icon_class(self):
        """Return icon class based on notification type for UI styling"""
        icon_classes = {
            'ORDER_STATUS': 'fa-shopping-cart',
            'NEW_ORDER': 'fa-plus-circle',
            'DELIVERY_UPDATE': 'fa-truck',
            'SYSTEM': 'fa-bell'
        }
        return icon_classes.get(self.type, 'fa-bell')
