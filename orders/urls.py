from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order management (general)
    path('', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/status/', views.order_status, name='order_status'),
    
    # Order creation and modification
    path('create/', views.order_create, name='order_create'),
    path('<int:order_id>/update/', views.order_update, name='order_update'),
    path('<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),
    
    # Order item management
    path('<int:order_id>/items/add/', views.order_item_add, name='order_item_add'),
    path('<int:order_id>/items/<int:item_id>/update/', views.order_item_update, name='order_item_update'),
    path('<int:order_id>/items/<int:item_id>/remove/', views.order_item_remove, name='order_item_remove'),
    
    # Order operations
    path('<int:order_id>/confirm/', views.order_confirm, name='order_confirm'),
    path('<int:order_id>/submit/', views.order_submit, name='order_submit'),
    path('<int:order_id>/reorder/', views.order_reorder, name='order_reorder'),
    path('<int:order_id>/print/', views.order_print, name='order_print'),
    
    # API endpoints
    path('api/status-update/', views.api_status_update, name='api_status_update'),
    path('api/stats/', views.api_order_stats, name='api_order_stats'),
]
