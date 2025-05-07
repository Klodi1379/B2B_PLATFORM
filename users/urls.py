from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Dashboard view (redirects to appropriate dashboard based on user type)
    path('dashboard/', views.dashboard, name='dashboard'),

    # User profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # User registration and activation
    path('register/', views.register, name='register'),
    path('register/<str:user_type>/', views.register_user_type, name='register_user_type'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),

    # Password change/reset
    path('password-change/', views.password_change, name='password_change'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/<str:uidb64>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),

    # Logout
    path('logout/', views.logout_view, name='logout'),

    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
