from django.db import models
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(models.Model):
    """Abstract base model that provides timestamping fields"""
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        abstract = True


class Address(models.Model):
    """Common address model that can be used by different entities"""
    street_address = models.CharField(_('Street Address'), max_length=255)
    city = models.CharField(_('City'), max_length=100)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    country = models.CharField(_('Country'), max_length=100)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Generic relation
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        
    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country}"


class Configuration(models.Model):
    """System-wide configuration settings"""
    key = models.CharField(_('Key'), max_length=100, unique=True)
    value = models.TextField(_('Value'))
    description = models.TextField(_('Description'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Configuration')
        verbose_name_plural = _('Configurations')
        
    def __str__(self):
        return self.key
