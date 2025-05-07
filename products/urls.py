from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product listings (general)
    path('', views.product_list, name='product_list'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Category views
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    
    # Search
    path('search/', views.product_search, name='product_search'),
    
    # API endpoints
    path('api/search/', views.api_product_search, name='api_product_search'),
    path('api/categories/', views.api_category_list, name='api_category_list'),
]
