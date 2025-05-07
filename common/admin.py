from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Address, Configuration

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('street_address', 'city', 'country', 'content_type', 'created_at')
    list_filter = ('city', 'country')
    search_fields = ('street_address', 'city', 'country', 'postal_code')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('street_address', 'city', 'postal_code', 'country')}),
        (_('Coordinates'), {'fields': ('latitude', 'longitude')}),
        (_('Related Object'), {'fields': ('content_type', 'object_id')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('key', 'value', 'description')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
