from django.urls import path
from . import views

app_name = 'shops'

urlpatterns = [
    # Shop Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Shop Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Supplier Management
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:supplier_id>/remove/', views.supplier_remove, name='supplier_remove'),

    # Catalog Browsing
    path('suppliers/<int:supplier_id>/catalog/', views.supplier_catalog, name='supplier_catalog'),
    path('suppliers/<int:supplier_id>/catalog/categories/<int:category_id>/', views.supplier_catalog_category, name='supplier_catalog_category'),
    path('suppliers/<int:supplier_id>/catalog/products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('suppliers/<int:supplier_id>/catalog/search/', views.catalog_search, name='catalog_search'),

    # Shopping Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('cart/switch-supplier/', views.cart_switch_supplier, name='cart_switch_supplier'),

    # Order Management
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/submit/', views.order_submit, name='submit_order'),
    path('orders/<int:order_id>/reorder/', views.order_reorder, name='reorder'),
    path('orders/<int:order_id>/cancel/', views.order_cancel, name='cancel_order'),
    path('orders/<int:order_id>/message/', views.add_order_message, name='add_order_message'),
    path('orders/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),

    # Delivery Tracking
    path('delivery/<int:delivery_id>/track/', views.track_delivery, name='track_delivery'),

    # API Endpoints
    path('api/quick-reorder/', views.api_quick_reorder, name='api_quick_reorder'),
]
