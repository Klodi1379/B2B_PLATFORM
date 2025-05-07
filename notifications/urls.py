from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification management
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('<int:notification_id>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
    path('mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('clear-all/', views.notification_clear_all, name='notification_clear_all'),
    
    # API endpoints
    path('api/count/', views.api_notification_count, name='api_notification_count'),
    path('api/recent/', views.api_notification_recent, name='api_notification_recent'),
]
