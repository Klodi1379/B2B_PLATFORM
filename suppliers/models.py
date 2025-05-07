from django.db import models
from django.utils.translation import gettext_lazy as _

class Supplier(models.Model):
    """Represents a supplier/distributor business"""
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    address = models.TextField(_('Address'))
    city = models.CharField(_('City'), max_length=100)
    country = models.CharField(_('Country'), max_length=100)
    tax_id = models.CharField(_('Tax ID'), max_length=50, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Phone'), max_length=20)
    logo = models.ImageField(_('Logo'), upload_to='supplier_logos/', blank=True, null=True)
    
    # Relations
    admin = models.ForeignKey(
        'users.User', 
        on_delete=models.PROTECT, 
        related_name='managed_suppliers',
        verbose_name=_('Admin')
    )
    
    # Timestamps and metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['name']

    def __str__(self):
        return self.name
