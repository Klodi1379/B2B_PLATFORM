from django.db import models
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    """Product category"""
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
        verbose_name=_('Parent Category')
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier', 
        on_delete=models.CASCADE, 
        related_name='categories',
        verbose_name=_('Supplier')
    )
    
    # Timestamps and metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        unique_together = ('name', 'supplier')
        ordering = ['name']
        
    def __str__(self):
        return self.name
        
    def get_full_path(self):
        """Return the full category path (including parents)"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

class Product(models.Model):
    """Product in a supplier's catalog"""
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    sku = models.CharField(_('SKU'), max_length=50, blank=True)
    barcode = models.CharField(_('Barcode'), max_length=50, blank=True)
    unit = models.CharField(_('Unit'), max_length=20)  # piece, kg, liter, etc.
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2)
    image = models.ImageField(_('Image'), upload_to='product_images/', blank=True, null=True)
    is_available = models.BooleanField(_('Available'), default=True)
    min_order_quantity = models.PositiveIntegerField(_('Minimum Order Quantity'), default=1)
    
    # Relations
    supplier = models.ForeignKey(
        'suppliers.Supplier', 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name=_('Supplier')
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products',
        verbose_name=_('Category')
    )
    
    # Timestamps and metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        unique_together = ('sku', 'supplier')
        ordering = ['name']
        
    def __str__(self):
        return self.name
        
    def get_formatted_price(self):
        """Return formatted price with currency symbol"""
        return f"{self.price} Lekë"
