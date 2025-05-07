from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    # Delivery plan management
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:plan_id>/', views.plan_detail, name='plan_detail'),
    path('plans/<int:plan_id>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:plan_id>/delete/', views.plan_delete, name='plan_delete'),
    
    # Delivery stop management
    path('plans/<int:plan_id>/stops/add/', views.stop_add, name='stop_add'),
    path('plans/<int:plan_id>/stops/<int:stop_id>/edit/', views.stop_edit, name='stop_edit'),
    path('plans/<int:plan_id>/stops/<int:stop_id>/remove/', views.stop_remove, name='stop_remove'),
    path('plans/<int:plan_id>/stops/reorder/', views.stop_reorder, name='stop_reorder'),
    
    # Delivery plan operations
    path('plans/<int:plan_id>/optimize/', views.plan_optimize, name='plan_optimize'),
    path('plans/<int:plan_id>/complete/', views.plan_complete, name='plan_complete'),
    path('plans/<int:plan_id>/print/', views.plan_print, name='plan_print'),
    
    # Delivery stop operations
    path('stops/<int:stop_id>/', views.stop_detail, name='stop_detail'),
    path('stops/<int:stop_id>/status-update/', views.stop_status_update, name='stop_status_update'),
    
    # Driver interface
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/today/', views.driver_today, name='driver_today'),
    path('driver/history/', views.driver_history, name='driver_history'),
    
    # API endpoints
    path('api/optimize-route/', views.api_optimize_route, name='api_optimize_route'),
    path('api/update-stop-status/', views.api_stop_status_update, name='api_stop_status_update'),
]
