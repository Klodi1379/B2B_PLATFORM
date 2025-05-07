from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    # Supplier Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Supplier Profile Management
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Catalog Management
    path('catalog/', views.catalog_list, name='catalog_list'),
    path('catalog/create/', views.product_create, name='product_create'),
    path('catalog/<int:product_id>/', views.product_detail, name='product_detail'),
    path('catalog/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('catalog/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('catalog/import/', views.catalog_import, name='catalog_import'),
    path('catalog/export/', views.catalog_export, name='catalog_export'),

    # Category Management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),

    # Customer (Shop) Management
    path('shops/', views.shop_list, name='shop_list'),
    path('shops/create/', views.shop_create, name='shop_create'),
    path('shops/<int:shop_id>/', views.shop_detail, name='shop_detail'),
    path('shops/<int:shop_id>/edit/', views.shop_edit, name='shop_edit'),
    path('shops/<int:shop_id>/deactivate/', views.shop_deactivate, name='shop_deactivate'),

    # Order Management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', views.order_update_status, name='order_update_status'),
    path('orders/<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),
    path('orders/<int:order_id>/print/', views.order_print, name='order_print'),
    path('orders/export/', views.order_export, name='order_export'),

    # Delivery Management
    path('delivery/', views.delivery_list, name='delivery_list'),
    path('delivery/create/', views.delivery_create, name='delivery_create'),
    path('delivery/<int:plan_id>/', views.delivery_detail, name='delivery_detail'),
    path('delivery/<int:plan_id>/edit/', views.delivery_edit, name='delivery_edit'),
    path('delivery/<int:plan_id>/generate-list/', views.delivery_generate_list, name='delivery_generate_list'),
    path('delivery/<int:plan_id>/print/', views.delivery_print, name='delivery_print'),

    # API Endpoints
    path('api/stats/daily-orders/', views.api_daily_orders, name='api_daily_orders'),
    path('api/stats/revenue/', views.api_revenue, name='api_revenue'),
]
