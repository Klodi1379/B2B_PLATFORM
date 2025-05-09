from django.urls import path
from . import views
from .views.health import health_check

app_name = 'common'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('search/', views.global_search, name='global_search'),
    path('settings/', views.system_settings, name='system_settings'),

    # Health check endpoint for Docker/Kubernetes
    path('health/', health_check, name='health_check'),
]
