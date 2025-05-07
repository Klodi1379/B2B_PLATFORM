from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Extended user model with role-based access control"""
    USER_TYPE_CHOICES = (
        ('ADMIN', _('Administrator')),
        ('SUPPLIER', _('Furnitor')),
        ('SHOP', _('Dyqan')),
        ('DRIVER', _('Shofer/Agjent')),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps and metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return self.username
    
    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'
    
    @property
    def is_supplier(self):
        return self.user_type == 'SUPPLIER'
    
    @property
    def is_shop(self):
        return self.user_type == 'SHOP'
    
    @property
    def is_driver(self):
        return self.user_type == 'DRIVER'
