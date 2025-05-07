from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product', 'quantity', 'unit_price', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'supplier', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'supplier', 'created_at', 'delivery_date')
    search_fields = ('shop__name', 'supplier__name', 'id')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'total_amount')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {'fields': ('shop', 'supplier', 'status')}),
        (_('Order Details'), {'fields': ('notes', 'total_amount')}),
        (_('Delivery Information'), {'fields': ('delivery_date', 'delivery_time_window')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at', 'submitted_at'), 'classes': ('collapse',)}),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product__name')
    readonly_fields = ('total_price',)
