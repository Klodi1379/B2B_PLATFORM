from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Supplier
from .forms import ProductForm, CategoryForm
from products.models import Product, Category
from shops.models import Shop
from orders.models import Order
from delivery.models import DeliveryPlan
from users.models import User

@login_required
def dashboard(request):
    """
    Supplier dashboard with overview of orders, clients, and deliveries
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access the supplier dashboard.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get today's date for the dashboard
    today_date = timezone.now().date()

    # Get recent orders with focus on new and confirmed orders
    recent_orders = Order.objects.filter(
        supplier=supplier,
        status__in=['SUBMITTED', 'CONFIRMED']
    ).order_by('-created_at')[:5]

    # Get all recent orders for the timeline
    all_recent_orders = Order.objects.filter(
        supplier=supplier
    ).order_by('-created_at')[:10]

    # Get upcoming deliveries
    upcoming_deliveries = DeliveryPlan.objects.filter(
        supplier=supplier,
        is_completed=False,
        date__gte=today_date
    ).order_by('date')[:3]

    # Get shop count
    shop_count = Order.objects.filter(supplier=supplier).values('shop').distinct().count()

    # Get product count
    product_count = Product.objects.filter(supplier=supplier).count()
    available_product_count = Product.objects.filter(supplier=supplier, is_available=True).count()

    # Get order counts by status
    order_counts = {}
    for status_code, status_name in Order.ORDER_STATUS_CHOICES:
        order_counts[status_code] = Order.objects.filter(supplier=supplier, status=status_code).count()

    # Get orders requiring attention (new submissions, etc.)
    attention_required = Order.objects.filter(
        supplier=supplier,
        status__in=['SUBMITTED', 'CONFIRMED']
    ).count()

    # Get today's orders
    orders_today = Order.objects.filter(
        supplier=supplier,
        created_at__date=today_date
    ).count()

    # Get today's revenue
    revenue_today = Order.objects.filter(
        supplier=supplier,
        created_at__date=today_date,
        status__in=['SUBMITTED', 'CONFIRMED', 'PROCESSING', 'READY', 'DELIVERING', 'DELIVERED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        'supplier': supplier,
        'today_date': today_date,
        'recent_orders': recent_orders,
        'all_recent_orders': all_recent_orders,
        'upcoming_deliveries': upcoming_deliveries,
        'shop_count': shop_count,
        'product_count': product_count,
        'available_product_count': available_product_count,
        'order_counts': order_counts,
        'attention_required': attention_required,
        'orders_today': orders_today,
        'revenue_today': revenue_today,
    }

    return render(request, 'suppliers/dashboard.html', context)

@login_required
def profile(request):
    """
    Display supplier profile information
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    supplier = get_object_or_404(Supplier, admin=request.user)

    return render(request, 'suppliers/profile.html', {'supplier': supplier})

@login_required
def profile_edit(request):
    """
    Edit supplier profile information
    """
    # Placeholder for profile edit functionality
    return render(request, 'suppliers/profile_edit.html')

# Catalog Management Views

@login_required
def catalog_list(request):
    """
    List all products in the supplier's catalog
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get all products for this supplier
    products = Product.objects.filter(supplier=supplier).order_by('name')

    # Apply filters if specified
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = Category.objects.get(id=category_id, supplier=supplier)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            pass

    # Search filter
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )

    # Get all categories for this supplier for the filter dropdown
    categories = Category.objects.filter(supplier=supplier)

    context = {
        'supplier': supplier,
        'products': products,
        'categories': categories,
        'selected_category_id': category_id,
        'query': query,
    }

    return render(request, 'suppliers/products/product_list.html', context)

@login_required
def product_create(request):
    """
    Create a new product in the supplier's catalog
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, supplier=supplier)
        if form.is_valid():
            product = form.save(commit=False)
            product.supplier = supplier
            product.save()
            messages.success(request, _('Product created successfully.'))
            return redirect('suppliers:catalog_list')
    else:
        form = ProductForm(supplier=supplier)

    context = {
        'supplier': supplier,
        'form': form,
        'title': _('Create New Product'),
    }

    return render(request, 'suppliers/products/product_form.html', context)

@login_required
def product_detail(request, product_id):
    """
    View details of a product
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the product, ensuring it belongs to this supplier
    product = get_object_or_404(Product, id=product_id, supplier=supplier)

    context = {
        'supplier': supplier,
        'product': product,
    }

    return render(request, 'suppliers/products/product_detail.html', context)

@login_required
def product_edit(request, product_id):
    """
    Edit a product
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the product, ensuring it belongs to this supplier
    product = get_object_or_404(Product, id=product_id, supplier=supplier)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, supplier=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, _('Product updated successfully.'))
            return redirect('suppliers:product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product, supplier=supplier)

    context = {
        'supplier': supplier,
        'product': product,
        'form': form,
        'title': _('Edit Product'),
    }

    return render(request, 'suppliers/products/product_form.html', context)

@login_required
def product_delete(request, product_id):
    """
    Delete a product
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the product, ensuring it belongs to this supplier
    product = get_object_or_404(Product, id=product_id, supplier=supplier)

    if request.method == 'POST':
        # Check if product is used in any orders
        if product.order_items.exists():
            # Instead of deleting, mark as unavailable
            product.is_available = False
            product.save()
            messages.warning(request, _('Product has been marked as unavailable because it is used in orders.'))
        else:
            # Safe to delete
            product.delete()
            messages.success(request, _('Product deleted successfully.'))

        return redirect('suppliers:catalog_list')

    context = {
        'supplier': supplier,
        'product': product,
    }

    return render(request, 'suppliers/products/product_confirm_delete.html', context)

@login_required
def catalog_import(request):
    """
    Import products to the catalog
    """
    # Placeholder for catalog import functionality
    return render(request, 'suppliers/catalog_import.html')

@login_required
def catalog_export(request):
    """
    Export the catalog
    """
    # Placeholder for catalog export functionality
    return HttpResponse('Catalog Export')

# Category Management Views

@login_required
def category_list(request):
    """
    List all categories
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get all categories for this supplier
    categories = Category.objects.filter(supplier=supplier).order_by('name')

    # Search filter
    query = request.GET.get('q')
    if query:
        categories = categories.filter(name__icontains=query)

    context = {
        'supplier': supplier,
        'categories': categories,
        'query': query,
    }

    return render(request, 'suppliers/products/category_list.html', context)

@login_required
def category_create(request):
    """
    Create a new category
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    if request.method == 'POST':
        form = CategoryForm(request.POST, supplier=supplier)
        if form.is_valid():
            category = form.save(commit=False)
            category.supplier = supplier
            category.save()
            messages.success(request, _('Category created successfully.'))
            return redirect('suppliers:category_list')
    else:
        form = CategoryForm(supplier=supplier)

    context = {
        'supplier': supplier,
        'form': form,
        'title': _('Create New Category'),
    }

    return render(request, 'suppliers/products/category_form.html', context)

@login_required
def category_detail(request, category_id):
    """
    View details of a category
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the category, ensuring it belongs to this supplier
    category = get_object_or_404(Category, id=category_id, supplier=supplier)

    # Get products in this category
    products = Product.objects.filter(category=category, supplier=supplier)

    context = {
        'supplier': supplier,
        'category': category,
        'products': products,
    }

    return render(request, 'suppliers/products/category_detail.html', context)

@login_required
def category_edit(request, category_id):
    """
    Edit a category
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the category, ensuring it belongs to this supplier
    category = get_object_or_404(Category, id=category_id, supplier=supplier)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, supplier=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, _('Category updated successfully.'))
            return redirect('suppliers:category_detail', category_id=category.id)
    else:
        form = CategoryForm(instance=category, supplier=supplier)

    context = {
        'supplier': supplier,
        'category': category,
        'form': form,
        'title': _('Edit Category'),
    }

    return render(request, 'suppliers/products/category_form.html', context)

@login_required
def category_delete(request, category_id):
    """
    Delete a category
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the category, ensuring it belongs to this supplier
    category = get_object_or_404(Category, id=category_id, supplier=supplier)

    if request.method == 'POST':
        # Check if category has products
        if Product.objects.filter(category=category).exists():
            messages.error(request, _('Cannot delete category that has products. Please reassign or delete the products first.'))
        else:
            category.delete()
            messages.success(request, _('Category deleted successfully.'))

        return redirect('suppliers:category_list')

    context = {
        'supplier': supplier,
        'category': category,
    }

    return render(request, 'suppliers/products/category_confirm_delete.html', context)

# Shop Management Views

@login_required
def shop_list(request):
    """
    List all shops associated with the supplier
    """
    # Placeholder for shop list functionality
    return render(request, 'suppliers/shop_list.html')

@login_required
def shop_create(request):
    """
    Create a new shop
    """
    # Placeholder for shop create functionality
    return render(request, 'suppliers/shop_create.html')

@login_required
def shop_detail(request, shop_id):
    """
    View details of a shop
    """
    # Placeholder for shop detail functionality
    return render(request, 'suppliers/shop_detail.html')

@login_required
def shop_edit(request, shop_id):
    """
    Edit a shop
    """
    # Placeholder for shop edit functionality
    return render(request, 'suppliers/shop_edit.html')

@login_required
def shop_deactivate(request, shop_id):
    """
    Deactivate a shop
    """
    # Placeholder for shop deactivate functionality
    return redirect('suppliers:shop_list')

# Order Management Views

@login_required
def order_list(request):
    """
    List all orders for the supplier
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get all orders for this supplier
    orders = Order.objects.filter(supplier=supplier).order_by('-created_at')

    # Apply filters if specified
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    shop_id = request.GET.get('shop')
    if shop_id:
        orders = orders.filter(shop_id=shop_id)

    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=date_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # Get all shops that have ordered from this supplier for the filter dropdown
    shops = Shop.objects.filter(orders__supplier=supplier).distinct()

    context = {
        'supplier': supplier,
        'orders': orders,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'shops': shops,
        'selected_status': status,
        'selected_shop_id': shop_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'suppliers/orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """
    View details of an order
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the order, ensuring it belongs to this supplier
    order = get_object_or_404(Order, id=order_id, supplier=supplier)

    # Get all items for this order
    order_items = order.items.all()

    # Initialize status update form
    from orders.forms import OrderStatusForm
    status_form = OrderStatusForm(initial={'status': order.status})

    context = {
        'supplier': supplier,
        'order': order,
        'order_items': order_items,
        'status_form': status_form,
    }

    return render(request, 'suppliers/orders/order_detail.html', context)

@login_required
def order_update_status(request, order_id):
    """
    Update the status of an order
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the order, ensuring it belongs to this supplier
    order = get_object_or_404(Order, id=order_id, supplier=supplier)

    if request.method == 'POST':
        from orders.forms import OrderStatusForm
        form = OrderStatusForm(request.POST)

        if form.is_valid():
            old_status = order.status
            new_status = form.cleaned_data['status']

            # Update order status
            order.status = new_status

            # If status changed to SUBMITTED, set submitted_at timestamp
            if new_status == 'SUBMITTED' and not order.submitted_at:
                order.submitted_at = timezone.now()

            order.save()

            # Send notification
            from notifications.tasks import send_order_status_notification
            send_order_status_notification.delay(order.id, old_status, new_status)

            messages.success(request, _('Order status updated successfully.'))
        else:
            messages.error(request, _('Error updating order status.'))

    return redirect('suppliers:order_detail', order_id=order.id)

@login_required
def order_cancel(request, order_id):
    """
    Cancel an order
    """
    # Ensure user is a supplier
    if not request.user.is_supplier:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get supplier associated with the user
    supplier = get_object_or_404(Supplier, admin=request.user)

    # Get the order, ensuring it belongs to this supplier
    order = get_object_or_404(Order, id=order_id, supplier=supplier)

    # Check if order can be cancelled
    if order.status not in ['DRAFT', 'SUBMITTED', 'CONFIRMED']:
        messages.error(request, _('This order cannot be cancelled.'))
        return redirect('suppliers:order_detail', order_id=order.id)

    if request.method == 'POST':
        # Update order status
        old_status = order.status
        order.status = 'CANCELLED'
        order.save()

        # Send notification
        from notifications.tasks import send_order_status_notification
        send_order_status_notification.delay(order.id, old_status, 'CANCELLED')

        messages.success(request, _('Order cancelled successfully.'))
        return redirect('suppliers:order_detail', order_id=order.id)

    context = {
        'supplier': supplier,
        'order': order,
    }

    return render(request, 'suppliers/orders/order_cancel.html', context)

@login_required
def order_print(request, order_id):
    """
    Print an order
    """
    # Placeholder for order print functionality
    return HttpResponse('Order Print')

@login_required
def order_export(request):
    """
    Export orders
    """
    # Placeholder for order export functionality
    return HttpResponse('Order Export')

# Delivery Management Views

@login_required
def delivery_list(request):
    """
    List all delivery plans
    """
    # Placeholder for delivery list functionality
    return render(request, 'suppliers/delivery_list.html')

@login_required
def delivery_create(request):
    """
    Create a new delivery plan
    """
    # Placeholder for delivery create functionality
    return render(request, 'suppliers/delivery_create.html')

@login_required
def delivery_detail(request, plan_id):
    """
    View details of a delivery plan
    """
    # Placeholder for delivery detail functionality
    return render(request, 'suppliers/delivery_detail.html')

@login_required
def delivery_edit(request, plan_id):
    """
    Edit a delivery plan
    """
    # Placeholder for delivery edit functionality
    return render(request, 'suppliers/delivery_edit.html')

@login_required
def delivery_generate_list(request, plan_id):
    """
    Generate a delivery list
    """
    # Placeholder for delivery list generation functionality
    return redirect('suppliers:delivery_detail', plan_id=plan_id)

@login_required
def delivery_print(request, plan_id):
    """
    Print a delivery plan
    """
    # Placeholder for delivery plan print functionality
    return HttpResponse('Delivery Plan Print')

# API Views

@login_required
def api_daily_orders(request):
    """
    API endpoint for daily order stats
    """
    # Placeholder for daily order stats API
    return JsonResponse({'status': 'success', 'data': []})

@login_required
def api_revenue(request):
    """
    API endpoint for revenue stats
    """
    # Placeholder for revenue stats API
    return JsonResponse({'status': 'success', 'data': []})
