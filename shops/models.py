from django.db import models
from django.utils.translation import gettext_lazy as _

class Shop(models.Model):
    """Represents a retail shop/store"""
    name = models.CharField(_('Name'), max_length=100)
    shop_type = models.CharField(_('Shop Type'), max_length=50)  # minimarket, kiosk, etc.
    address = models.TextField(_('Address'))
    city = models.CharField(_('City'), max_length=100)
    country = models.CharField(_('Country'), max_length=100)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    tax_id = models.CharField(_('Tax ID'), max_length=50, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Phone'), max_length=20)
    
    # Relations
    admin = models.ForeignKey(
        'users.User', 
        on_delete=models.PROTECT, 
        related_name='managed_shops',
        verbose_name=_('Admin')
    )
    
    # Timestamps and metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Shop')
        verbose_name_plural = _('Shops')
        ordering = ['name']

    def __str__(self):
        return self.name
        
    def get_location(self):
        """Return a tuple of latitude and longitude if both exist"""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None
