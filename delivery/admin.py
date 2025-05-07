from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import DeliveryPlan, DeliveryStop

class DeliveryStopInline(admin.TabularInline):
    model = DeliveryStop
    extra = 0
    fields = ('shop', 'order', 'position', 'status', 'estimated_arrival_time', 'actual_arrival_time')

@admin.register(DeliveryPlan)
class DeliveryPlanAdmin(admin.ModelAdmin):
    list_display = ('date', 'supplier', 'driver', 'stop_count', 'is_completed')
    list_filter = ('is_completed', 'date', 'supplier')
    search_fields = ('supplier__name', 'driver__username', 'driver__first_name', 'driver__last_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    inlines = [DeliveryStopInline]
    fieldsets = (
        (None, {'fields': ('supplier', 'driver', 'date')}),
        (_('Details'), {'fields': ('notes', 'is_completed')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def stop_count(self, obj):
        return obj.stops.count()
    stop_count.short_description = _('Stops')

@admin.register(DeliveryStop)
class DeliveryStopAdmin(admin.ModelAdmin):
    list_display = ('delivery_plan', 'position', 'shop', 'order', 'status')
    list_filter = ('status', 'delivery_plan__date')
    search_fields = ('shop__name', 'notes')
    readonly_fields = ('delivery_plan',)
    fieldsets = (
        (None, {'fields': ('delivery_plan', 'shop', 'order')}),
        (_('Positioning'), {'fields': ('position',)}),
        (_('Status and Timing'), {'fields': ('status', 'estimated_arrival_time', 'actual_arrival_time')}),
        (_('Notes'), {'fields': ('notes',)}),
    )
