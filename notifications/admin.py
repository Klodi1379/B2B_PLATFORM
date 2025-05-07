from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read', 'type', 'created_at')
    search_fields = ('title', 'message', 'recipient__username', 'recipient__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {'fields': ('recipient', 'type', 'title', 'message')}),
        (_('Related Objects'), {'fields': ('order', 'delivery_plan')}),
        (_('Status'), {'fields': ('is_read',)}),
        (_('Timestamps'), {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
