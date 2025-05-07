from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'phone', 'admin', 'is_active')
    list_filter = ('is_active', 'city', 'country', 'created_at')
    search_fields = ('name', 'address', 'email', 'phone')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'logo', 'admin')}),
        (_('Contact Information'), {'fields': ('email', 'phone')}),
        (_('Address'), {'fields': ('address', 'city', 'country')}),
        (_('Business Information'), {'fields': ('tax_id',)}),
        (_('Status'), {'fields': ('is_active',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
