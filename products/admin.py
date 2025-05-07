from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'parent', 'product_count')
    list_filter = ('supplier',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Products')

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0
    fields = ('name', 'parent')
    verbose_name = _('Subcategory')
    verbose_name_plural = _('Subcategories')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'supplier', 'category', 'price', 'is_available')
    list_filter = ('is_available', 'supplier', 'category')
    search_fields = ('name', 'description', 'sku', 'barcode')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'image')}),
        (_('Categorization'), {'fields': ('supplier', 'category')}),
        (_('Pricing and Units'), {'fields': ('price', 'unit', 'min_order_quantity')}),
        (_('Identifiers'), {'fields': ('sku', 'barcode')}),
        (_('Status'), {'fields': ('is_available',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    list_per_page = 50
