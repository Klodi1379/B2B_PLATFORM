from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import Order, OrderItem
from .forms import OrderForm, OrderItemForm, OrderStatusForm, OrderFilterForm
from products.models import Product
from notifications.tasks import send_order_status_notification

@login_required
def order_list(request):
    """
    List all orders for the current user (filtered by role)
    """
    user = request.user
    
    # Initialize filter form
    filter_form = OrderFilterForm(request.GET, user=user)
    
    # Base queryset depends on user type
    if user.is_supplier:
        # Supplier users see orders for their supplier
        supplier = user.managed_suppliers.first()
        if not supplier:
            messages.error(request, _("You don't have any supplier associated with your account."))
            return redirect('users:dashboard')
        
        orders = Order.objects.filter(supplier=supplier)
    elif user.is_shop:
        # Shop users see their shop's orders
        shop = user.managed_shops.first()
        if not shop:
            messages.error(request, _("You don't have any shop associated with your account."))
            return redirect('users:dashboard')
        
        orders = Order.objects.filter(shop=shop)
    else:
        # Admin users see all orders
        orders = Order.objects.all()
    
    # Apply filters if the form is valid
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        # Status filter
        if data.get('status'):
            orders = orders.filter(status=data['status'])
        
        # Date range filters
        if data.get('date_from'):
            orders = orders.filter(created_at__date__gte=data['date_from'])
        
        if data.get('date_to'):
            orders = orders.filter(created_at__date__lte=data['date_to'])
        
        # Shop filter (for supplier users)
        if user.is_supplier and data.get('shop'):
            orders = orders.filter(shop=data['shop'])
        
        # Supplier filter (for shop users)
        if user.is_shop and data.get('supplier'):
            orders = orders.filter(supplier=data['supplier'])
    
    # Order by created_at (newest first)
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'filter_form': filter_form,
    }
    
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """
    View details of an order
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user)
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user)
    else:
        order = get_object_or_404(Order, id=order_id)
    
    # Get all items for this order
    order_items = order.items.all()
    
    # Create status form for suppliers
    status_form = None
    if user.is_supplier and order.status != 'DELIVERED' and order.status != 'CANCELLED':
        status_form = OrderStatusForm(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_form': status_form,
    }
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_status(request, order_id):
    """
    Update the status of an order (for suppliers)
    """
    user = request.user
    
    # Only suppliers can update order status
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to update order status."))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, id=order_id, supplier__admin=user)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, order=order)
        if form.is_valid():
            old_status = order.status
            new_status = form.cleaned_data['status']
            
            # Update order status
            order.status = new_status
            
            # Set submitted_at timestamp if status changes to SUBMITTED
            if old_status != 'SUBMITTED' and new_status == 'SUBMITTED':
                order.submitted_at = timezone.now()
                
            order.save()
            
            # Send notification
            send_order_status_notification.delay(order.id, old_status, new_status)
            
            messages.success(request, _("Order status has been updated."))
            return redirect('orders:order_detail', order_id=order.id)
    
    # If not POST or form not valid, redirect to detail view
    return redirect('orders:order_detail', order_id=order.id)

@login_required
def order_create(request):
    """
    Create a new order
    """
    user = request.user
    
    # Initialize the order form
    form = OrderForm(request.POST or None, user=user)
    
    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        
        # If shop user, set the shop automatically
        if user.is_shop:
            shop = user.managed_shops.first()
            if shop:
                order.shop = shop
        
        # If supplier user, set the supplier automatically
        if user.is_supplier:
            supplier = user.managed_suppliers.first()
            if supplier:
                order.supplier = supplier
        
        order.save()
        
        messages.success(request, _("Order created successfully. Now add items to your order."))
        return redirect('orders:order_update', order_id=order.id)
    
    context = {
        'form': form,
        'title': _('Create New Order'),
    }
    
    return render(request, 'orders/order_form.html', context)

@login_required
def order_update(request, order_id):
    """
    Update an existing order (add/remove items)
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user, status='DRAFT')
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user, status='DRAFT')
    else:
        order = get_object_or_404(Order, id=order_id, status='DRAFT')
    
    # Get existing items
    order_items = order.items.all()
    
    # Initialize item form
    item_form = OrderItemForm(request.POST or None, order=order)
    
    if request.method == 'POST' and item_form.is_valid():
        item = item_form.save(commit=False)
        item.order = order
        
        # Set unit price from product if not provided
        if not item.unit_price:
            item.unit_price = item.product.price
            
        item.save()
        
        messages.success(request, _("Item added to order."))
        return redirect('orders:order_update', order_id=order.id)
    
    context = {
        'order': order,
        'order_items': order_items,
        'item_form': item_form,
    }
    
    return render(request, 'orders/order_update.html', context)

@login_required
def order_item_add(request, order_id):
    """
    Add an item to an order
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user, status='DRAFT')
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user, status='DRAFT')
    else:
        order = get_object_or_404(Order, id=order_id, status='DRAFT')
    
    # Initialize form
    form = OrderItemForm(request.POST or None, order=order)
    
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.order = order
        
        # Set unit price from product if not provided
        if not item.unit_price:
            item.unit_price = item.product.price
            
        item.save()
        
        messages.success(request, _("Item added to order."))
        return redirect('orders:order_update', order_id=order.id)
    
    # Redirect back to order update view
    return redirect('orders:order_update', order_id=order.id)

@login_required
def order_item_update(request, order_id, item_id):
    """
    Update an item in an order
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user, status='DRAFT')
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user, status='DRAFT')
    else:
        order = get_object_or_404(Order, id=order_id, status='DRAFT')
    
    # Get the item
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    # Initialize form
    form = OrderItemForm(request.POST or None, instance=item, order=order)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        
        messages.success(request, _("Item updated."))
        return redirect('orders:order_update', order_id=order.id)
    
    # Redirect back to order update view
    return redirect('orders:order_update', order_id=order.id)

@login_required
def order_item_remove(request, order_id, item_id):
    """
    Remove an item from an order
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user, status='DRAFT')
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user, status='DRAFT')
    else:
        order = get_object_or_404(Order, id=order_id, status='DRAFT')
    
    # Get the item
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    # Delete the item
    item.delete()
    
    messages.success(request, _("Item removed from order."))
    return redirect('orders:order_update', order_id=order.id)

@login_required
def order_confirm(request, order_id):
    """
    Confirm an order before submitting
    """
    user = request.user
    
    # Only shop users can confirm orders
    if not user.is_shop:
        messages.error(request, _("You don't have permission to confirm orders."))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, id=order_id, shop__admin=user, status='DRAFT')
    
    # Check if order has items
    if not order.items.exists():
        messages.error(request, _("Cannot confirm an empty order. Please add items first."))
        return redirect('orders:order_update', order_id=order.id)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    
    return render(request, 'orders/order_confirm.html', context)

@login_required
def order_submit(request, order_id):
    """
    Submit an order to the supplier
    """
    user = request.user
    
    # Only shop users can submit orders
    if not user.is_shop:
        messages.error(request, _("You don't have permission to submit orders."))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, id=order_id, shop__admin=user, status='DRAFT')
    
    # Check if order has items
    if not order.items.exists():
        messages.error(request, _("Cannot submit an empty order. Please add items first."))
        return redirect('orders:order_update', order_id=order.id)
    
    # Update order status and save submission time
    old_status = order.status
    order.status = 'SUBMITTED'
    order.submitted_at = timezone.now()
    order.save()
    
    # Send notification
    send_order_status_notification.delay(order.id, old_status, 'SUBMITTED')
    
    messages.success(request, _("Order submitted successfully."))
    return redirect('orders:order_detail', order_id=order.id)

@login_required
def order_reorder(request, order_id):
    """
    Create a new order based on a previous one
    """
    user = request.user
    
    # Only shop users can reorder
    if not user.is_shop:
        messages.error(request, _("You don't have permission to reorder."))
        return redirect('orders:order_list')
    
    # Get the original order
    original_order = get_object_or_404(Order, id=order_id, shop__admin=user)
    
    # Create a new order based on the original
    new_order = Order.objects.create(
        shop=original_order.shop,
        supplier=original_order.supplier,
        status='DRAFT'
    )
    
    # Copy items from original order
    for item in original_order.items.all():
        # Check if product is still available
        product = Product.objects.filter(id=item.product.id, is_available=True).first()
        if product:
            OrderItem.objects.create(
                order=new_order,
                product=product,
                quantity=item.quantity,
                unit_price=product.price  # Use current price
            )
    
    messages.success(request, _("Order copied successfully. You can now edit it before submitting."))
    return redirect('orders:order_update', order_id=new_order.id)

@login_required
def order_cancel(request, order_id):
    """
    Cancel an order
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user)
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user)
    else:
        order = get_object_or_404(Order, id=order_id)
    
    # Check if order can be cancelled
    if not order.can_be_cancelled():
        messages.error(request, _("This order cannot be cancelled."))
        return redirect('orders:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        old_status = order.status
        order.status = 'CANCELLED'
        order.save()
        
        # Send notification
        send_order_status_notification.delay(order.id, old_status, 'CANCELLED')
        
        messages.success(request, _("Order cancelled successfully."))
        return redirect('orders:order_detail', order_id=order.id)
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_cancel.html', context)

@login_required
def order_print(request, order_id):
    """
    Print an order
    """
    user = request.user
    
    # Access control based on user type
    if user.is_supplier:
        order = get_object_or_404(Order, id=order_id, supplier__admin=user)
    elif user.is_shop:
        order = get_object_or_404(Order, id=order_id, shop__admin=user)
    else:
        order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'print_view': True,
    }
    
    return render(request, 'orders/order_print.html', context)

# API endpoints

@login_required
def api_status_update(request):
    """
    API endpoint for updating order status
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})
    
    order_id = request.POST.get('order_id')
    new_status = request.POST.get('status')
    
    if not order_id or not new_status:
        return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})
    
    user = request.user
    
    # Only suppliers can update order status via API
    if not user.is_supplier:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})
    
    try:
        order = Order.objects.get(id=order_id, supplier__admin=user)
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'})
    
    # Check if status is valid
    valid_statuses = [status[0] for status in Order.ORDER_STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'})
    
    # Update order status
    old_status = order.status
    order.status = new_status
    
    # Set submitted_at timestamp if status changes to SUBMITTED
    if old_status != 'SUBMITTED' and new_status == 'SUBMITTED':
        order.submitted_at = timezone.now()
        
    order.save()
    
    # Send notification
    send_order_status_notification.delay(order.id, old_status, new_status)
    
    return JsonResponse({'status': 'success', 'message': 'Order status updated'})

@login_required
def api_order_stats(request):
    """
    API endpoint for order statistics
    """
    user = request.user
    
    # Base queryset depends on user type
    if user.is_supplier:
        # Supplier users see orders for their supplier
        supplier = user.managed_suppliers.first()
        if not supplier:
            return JsonResponse({'status': 'error', 'message': 'No supplier associated with account'})
        
        orders = Order.objects.filter(supplier=supplier)
    elif user.is_shop:
        # Shop users see their shop's orders
        shop = user.managed_shops.first()
        if not shop:
            return JsonResponse({'status': 'error', 'message': 'No shop associated with account'})
        
        orders = Order.objects.filter(shop=shop)
    else:
        # Admin users see all orders
        orders = Order.objects.all()
    
    # Get order stats
    total_orders = orders.count()
    total_revenue = orders.filter(status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get orders by status
    status_counts = {}
    for status_code, status_name in Order.ORDER_STATUS_CHOICES:
        status_counts[status_code] = orders.filter(status=status_code).count()
    
    # Get recent orders (last 7 days)
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    recent_orders = orders.filter(created_at__gte=seven_days_ago).count()
    
    data = {
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'status_counts': status_counts,
        'recent_orders': recent_orders,
    }
    
    return JsonResponse({'status': 'success', 'data': data})
