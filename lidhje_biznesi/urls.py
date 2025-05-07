"""
URL configuration for lidhje_biznesi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Application URLs
    path('suppliers/', include('suppliers.urls', namespace='suppliers')),
    path('shops/', include('shops.urls', namespace='shops')),
    path('products/', include('products.urls', namespace='products')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('delivery/', include('delivery.urls', namespace='delivery')),
    path('users/', include('users.urls', namespace='users')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    
    # Common URLs - this includes the home page
    path('', include('common.urls', namespace='common')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'common.views.error_404'
handler500 = 'common.views.error_500'
