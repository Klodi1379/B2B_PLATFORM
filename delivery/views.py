from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from decimal import Decimal
import logging

from .models import DeliveryPlan, DeliveryStop
from .forms import DeliveryPlanForm, DeliveryStopForm, DeliveryStopStatusForm, DeliveryPlanFilterForm, StopReorderForm
from .route_optimizer import get_optimizer
from orders.models import Order
from shops.models import Shop
from users.models import User
from notifications.tasks import send_delivery_notification

logger = logging.getLogger(__name__)

@login_required
def plan_list(request):
    """
    List all delivery plans
    """
    user = request.user

    # Initialize filter form
    filter_form = DeliveryPlanFilterForm(request.GET, supplier=user.managed_suppliers.first() if user.is_supplier else None)

    # Base queryset depends on user type
    if user.is_supplier:
        # Supplier users see their delivery plans
        supplier = user.managed_suppliers.first()
        if not supplier:
            messages.error(request, _("You don't have any supplier associated with your account."))
            return redirect('users:dashboard')

        plans = DeliveryPlan.objects.filter(supplier=supplier)
    elif user.is_driver:
        # Driver users see their assigned delivery plans
        plans = DeliveryPlan.objects.filter(driver=user)
    else:
        # Admin users see all delivery plans
        plans = DeliveryPlan.objects.all()

    # Apply filters if the form is valid
    if filter_form.is_valid():
        data = filter_form.cleaned_data

        # Completion status filter
        if data.get('completion_status') == 'completed':
            plans = plans.filter(is_completed=True)
        elif data.get('completion_status') == 'active':
            plans = plans.filter(is_completed=False)

        # Date range filters
        if data.get('date_from'):
            plans = plans.filter(date__gte=data['date_from'])

        if data.get('date_to'):
            plans = plans.filter(date__lte=data['date_to'])

        # Driver filter
        if data.get('driver'):
            plans = plans.filter(driver=data['driver'])

    # Order by date (newest first)
    plans = plans.order_by('-date')

    context = {
        'plans': plans,
        'filter_form': filter_form,
    }

    return render(request, 'delivery/plan_list.html', context)

@login_required
def plan_create(request):
    """
    Create a new delivery plan
    """
    user = request.user

    # Only suppliers can create delivery plans
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to create delivery plans."))
        return redirect('delivery:plan_list')

    supplier = user.managed_suppliers.first()
    if not supplier:
        messages.error(request, _("You don't have any supplier associated with your account."))
        return redirect('users:dashboard')

    # Initialize the form
    form = DeliveryPlanForm(request.POST or None, supplier=supplier)

    if request.method == 'POST' and form.is_valid():
        plan = form.save()

        # Send notification to driver if assigned
        if plan.driver:
            send_delivery_notification.delay(plan.id)

        messages.success(request, _("Delivery plan created successfully."))
        return redirect('delivery:plan_detail', plan_id=plan.id)

    context = {
        'form': form,
        'title': _('Create New Delivery Plan'),
    }

    return render(request, 'delivery/plan_form.html', context)

@login_required
def plan_detail(request, plan_id):
    """
    View details of a delivery plan
    """
    user = request.user

    # Access control based on user type
    if user.is_supplier:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user)
    elif user.is_driver:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, driver=user)
    else:
        plan = get_object_or_404(DeliveryPlan, id=plan_id)

    # Get all stops for this plan
    stops = plan.stops.all().order_by('position')

    # Create stop form for suppliers
    stop_form = None
    if user.is_supplier and not plan.is_completed:
        stop_form = DeliveryStopForm(delivery_plan=plan)

    # Create reorder form for suppliers
    reorder_form = None
    if user.is_supplier and not plan.is_completed and stops.exists():
        reorder_form = StopReorderForm(delivery_plan=plan)

    context = {
        'plan': plan,
        'stops': stops,
        'stop_form': stop_form,
        'reorder_form': reorder_form,
    }

    return render(request, 'delivery/plan_detail.html', context)

@login_required
def plan_edit(request, plan_id):
    """
    Edit a delivery plan
    """
    user = request.user

    # Only suppliers can edit delivery plans
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to edit delivery plans."))
        return redirect('delivery:plan_list')

    plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)

    # Initialize the form
    form = DeliveryPlanForm(request.POST or None, instance=plan, supplier=plan.supplier)

    if request.method == 'POST' and form.is_valid():
        updated_plan = form.save()

        # Send notification to driver if changed
        if 'driver' in form.changed_data and updated_plan.driver:
            send_delivery_notification.delay(updated_plan.id)

        messages.success(request, _("Delivery plan updated successfully."))
        return redirect('delivery:plan_detail', plan_id=updated_plan.id)

    context = {
        'form': form,
        'plan': plan,
        'title': _('Edit Delivery Plan'),
    }

    return render(request, 'delivery/plan_form.html', context)

@login_required
def plan_delete(request, plan_id):
    """
    Delete a delivery plan
    """
    user = request.user

    # Only suppliers can delete delivery plans
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to delete delivery plans."))
        return redirect('delivery:plan_list')

    plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user)

    # Check if plan has stops
    if plan.stops.exists():
        messages.error(request, _("Cannot delete a delivery plan with stops. Remove all stops first."))
        return redirect('delivery:plan_detail', plan_id=plan.id)

    if request.method == 'POST':
        plan.delete()
        messages.success(request, _("Delivery plan deleted successfully."))
        return redirect('delivery:plan_list')

    context = {
        'plan': plan,
    }

    return render(request, 'delivery/plan_delete.html', context)

@login_required
def stop_add(request, plan_id):
    """
    Add a stop to a delivery plan
    """
    user = request.user

    # Only suppliers can add stops
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to add stops."))
        return redirect('delivery:plan_list')

    plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)

    # Initialize the form
    form = DeliveryStopForm(request.POST or None, delivery_plan=plan)

    if request.method == 'POST' and form.is_valid():
        stop = form.save(commit=False)
        stop.delivery_plan = plan
        stop.save()

        messages.success(request, _("Stop added to delivery plan."))
        return redirect('delivery:plan_detail', plan_id=plan.id)

    context = {
        'form': form,
        'plan': plan,
        'title': _('Add Delivery Stop'),
    }

    return render(request, 'delivery/stop_form.html', context)

@login_required
def stop_edit(request, plan_id, stop_id):
    """
    Edit a stop in a delivery plan
    """
    user = request.user

    # Only suppliers can edit stops
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to edit stops."))
        return redirect('delivery:plan_list')

    plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)
    stop = get_object_or_404(DeliveryStop, id=stop_id, delivery_plan=plan)

    # Initialize the form
    form = DeliveryStopForm(request.POST or None, instance=stop, delivery_plan=plan)

    if request.method == 'POST' and form.is_valid():
        form.save()

        messages.success(request, _("Delivery stop updated successfully."))
        return redirect('delivery:plan_detail', plan_id=plan.id)

    context = {
        'form': form,
        'plan': plan,
        'stop': stop,
        'title': _('Edit Delivery Stop'),
    }

    return render(request, 'delivery/stop_form.html', context)

@login_required
def stop_remove(request, plan_id, stop_id):
    """
    Remove a stop from a delivery plan
    """
    user = request.user

    # Only suppliers can remove stops
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to remove stops."))
        return redirect('delivery:plan_list')

    plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)
    stop = get_object_or_404(DeliveryStop, id=stop_id, delivery_plan=plan)

    if request.method == 'POST':
        stop.delete()

        # Reorder remaining stops
        remaining_stops = plan.stops.all().order_by('position')
        for i, remaining_stop in enumerate(remaining_stops):
            remaining_stop.position = i + 1
            remaining_stop.save()

        messages.success(request, _("Delivery stop removed successfully."))
        return redirect('delivery:plan_detail', plan_id=plan.id)

    context = {
        'plan': plan,
        'stop': stop,
    }

    return render(request, 'delivery/stop_remove.html', context)

@login_required
def stop_reorder(request, plan_id):
    """
    Reorder stops in a delivery plan
    """
    user = request.user

    # Only suppliers can reorder stops
    if not user.is_supplier:
        messages.error(request, _("You don't have permission to reorder stops."))
        return redirect('delivery:plan_list')

    plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)

    if request.method == 'POST':
        form = StopReorderForm(request.POST, delivery_plan=plan)

        if form.is_valid():
            # Update positions for all stops
            for stop in plan.stops.all():
                position_field = f'stop_position_{stop.id}'
                if position_field in form.cleaned_data:
                    stop.position = form.cleaned_data[position_field]
                    stop.save()

            messages.success(request, _("Delivery stops reordered successfully."))
            return redirect('delivery:plan_detail', plan_id=plan.id)

    # Redirect back to plan detail
    return redirect('delivery:plan_detail', plan_id=plan.id)

@login_required
def plan_optimize(request, plan_id):
    """
    Optimize the route for a delivery plan
    """
    user = request.user

    # Only suppliers and drivers can optimize routes
    if not (user.is_supplier or user.is_driver):
        messages.error(request, _("You don't have permission to optimize routes."))
        return redirect('delivery:plan_list')

    # Get the delivery plan
    if user.is_supplier:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)
    else:  # Driver
        plan = get_object_or_404(DeliveryPlan, id=plan_id, driver=user, is_completed=False)

    # Check if plan has stops
    if not plan.stops.exists():
        messages.error(request, _("Cannot optimize an empty delivery plan. Add stops first."))
        return redirect('delivery:plan_detail', plan_id=plan.id)

    try:
        # Get the optimizer
        optimizer = get_optimizer()

        # Prepare the starting point (warehouse)
        start_point = {
            'lat': float(plan.warehouse_latitude or plan.supplier.latitude or 41.3275),  # Default to Tirana
            'lng': float(plan.warehouse_longitude or plan.supplier.longitude or 19.8187)
        }

        # Prepare the stops
        stops = []
        for stop in plan.stops.all().select_related('shop'):
            stops.append({
                'id': stop.id,
                'lat': float(stop.shop.latitude or 41.3275),  # Default to Tirana
                'lng': float(stop.shop.longitude or 19.8187),
                'priority': stop.priority,
                'time_window_start': stop.time_window_start.strftime('%H:%M') if stop.time_window_start else None,
                'time_window_end': stop.time_window_end.strftime('%H:%M') if stop.time_window_end else None
            })

        # Optimize the route
        result = optimizer.optimize_route(start_point, stops, return_to_start=True)

        # Update the stops with the optimized route
        for i, route_stop in enumerate(result['route']):
            stop = DeliveryStop.objects.get(id=route_stop['stop_id'])
            stop.position = i + 1

            # If the API returned distance and duration, update them
            if 'distance' in route_stop:
                stop.distance_from_previous = Decimal(str(route_stop['distance'] / 1000))  # Convert to km

            # If the API returned arrival times, update them
            if 'arrival_time' in route_stop:
                from datetime import datetime
                arrival_time = datetime.fromtimestamp(route_stop['arrival_time'] / 1000)  # Convert from milliseconds
                stop.estimated_arrival_time = arrival_time.time()

            stop.save()

        # Update the plan with the total distance and duration
        plan.total_distance = Decimal(str(result['total_distance']))
        plan.total_duration = Decimal(str(result['total_time']))
        plan.save()

        messages.success(request, _("Delivery route optimized successfully."))

    except Exception as e:
        logger.exception(f"Error optimizing route: {str(e)}")
        messages.error(request, _("Error optimizing route: {}").format(str(e)))

    return redirect('delivery:plan_detail', plan_id=plan.id)

@login_required
def plan_complete(request, plan_id):
    """
    Mark a delivery plan as completed
    """
    user = request.user

    # Access control based on user type
    if user.is_supplier:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user)
    elif user.is_driver:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, driver=user)
    else:
        messages.error(request, _("You don't have permission to complete delivery plans."))
        return redirect('delivery:plan_list')

    if request.method == 'POST':
        # Check if all stops are completed or skipped
        incomplete_stops = plan.stops.exclude(status__in=['COMPLETED', 'SKIPPED']).count()

        if incomplete_stops > 0:
            messages.error(request, _("Cannot complete delivery plan. There are still %(count)s incomplete stops.") % {'count': incomplete_stops})
            return redirect('delivery:plan_detail', plan_id=plan.id)

        plan.is_completed = True
        plan.save()

        messages.success(request, _("Delivery plan marked as completed."))
        return redirect('delivery:plan_list')

    context = {
        'plan': plan,
    }

    return render(request, 'delivery/plan_complete.html', context)

@login_required
def plan_print(request, plan_id):
    """
    Print a delivery plan
    """
    user = request.user

    # Access control based on user type
    if user.is_supplier:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user)
    elif user.is_driver:
        plan = get_object_or_404(DeliveryPlan, id=plan_id, driver=user)
    else:
        plan = get_object_or_404(DeliveryPlan, id=plan_id)

    # Get all stops for this plan
    stops = plan.stops.all().order_by('position')

    context = {
        'plan': plan,
        'stops': stops,
        'print_view': True,
    }

    return render(request, 'delivery/plan_print.html', context)

@login_required
@login_required
def stop_detail(request, stop_id):
    """
    View details of a delivery stop
    """
    user = request.user
    stop = get_object_or_404(DeliveryStop, id=stop_id)
    plan = stop.delivery_plan

    # Access control based on user type
    if user.is_supplier:
        if plan.supplier.admin != user:
            messages.error(request, _("You don't have permission to view this stop."))
            return redirect('delivery:plan_list')
    elif user.is_driver:
        if plan.driver != user:
            messages.error(request, _("You don't have permission to view this stop."))
            return redirect('delivery:driver_today')

    context = {
        'stop': stop,
        'plan': plan,
    }

    return render(request, 'delivery/stop_detail.html', context)

@login_required
def stop_status_update(request, stop_id):
    """
    Update the status of a delivery stop
    """
    user = request.user

    # Get the stop
    stop = get_object_or_404(DeliveryStop, id=stop_id)
    plan = stop.delivery_plan

    # Access control based on user type
    if user.is_supplier:
        if plan.supplier.admin != user:
            messages.error(request, _("You don't have permission to update this stop."))
            return redirect('delivery:plan_list')
    elif user.is_driver:
        if plan.driver != user:
            messages.error(request, _("You don't have permission to update this stop."))
            return redirect('delivery:plan_list')
    else:
        messages.error(request, _("You don't have permission to update delivery stops."))
        return redirect('delivery:plan_list')

    # Initialize the form
    form = DeliveryStopStatusForm(request.POST or None, stop=stop)

    if request.method == 'POST' and form.is_valid():
        # Update stop status
        stop.status = form.cleaned_data['status']
        stop.notes = form.cleaned_data['notes']

        # Set actual arrival time if status is ARRIVED and not already set
        if stop.status == 'ARRIVED' and not stop.actual_arrival_time:
            stop.actual_arrival_time = timezone.now().time()
        elif form.cleaned_data['actual_arrival_time']:
            stop.actual_arrival_time = form.cleaned_data['actual_arrival_time']

        stop.save()

        # Update order status if stop is completed
        if stop.status == 'COMPLETED' and stop.order.status in ['READY', 'DELIVERING']:
            stop.order.status = 'DELIVERED'
            stop.order.save()

            # Send notification for order status change
            from notifications.tasks import send_order_status_notification
            send_order_status_notification.delay(stop.order.id, 'DELIVERING', 'DELIVERED')

        messages.success(request, _("Delivery stop status updated successfully."))

        if user.is_driver:
            return redirect('delivery:driver_today')
        else:
            return redirect('delivery:plan_detail', plan_id=plan.id)

    context = {
        'form': form,
        'stop': stop,
        'plan': plan,
        'title': _('Update Stop Status'),
    }

    return render(request, 'delivery/stop_status_form.html', context)

@login_required
@login_required
def driver_dashboard(request):
    """
    Show the driver dashboard with overview of deliveries
    """
    user = request.user

    # Only drivers can access this view
    if not user.is_driver:
        messages.error(request, _("You don't have permission to access driver views."))
        return redirect('users:dashboard')

    # Get today's delivery plan
    today = timezone.now().date()
    today_plan = DeliveryPlan.objects.filter(driver=user, date=today, is_completed=False).first()

    # Get recent completed deliveries
    completed_plans = DeliveryPlan.objects.filter(
        driver=user,
        is_completed=True
    ).order_by('-date')[:5]

    # Get statistics
    total_deliveries = DeliveryPlan.objects.filter(driver=user).count()
    completed_deliveries = DeliveryPlan.objects.filter(driver=user, is_completed=True).count()
    completion_rate = (completed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

    context = {
        'today_plan': today_plan,
        'completed_plans': completed_plans,
        'total_deliveries': total_deliveries,
        'completed_deliveries': completed_deliveries,
        'completion_rate': completion_rate,
    }

    return render(request, 'delivery/driver_dashboard.html', context)

@login_required
def driver_today(request):
    """
    Show today's delivery plan for a driver
    """
    user = request.user

    # Only drivers can access this view
    if not user.is_driver:
        messages.error(request, _("You don't have permission to access driver views."))
        return redirect('users:dashboard')

    # Get today's delivery plan
    today = timezone.now().date()
    plan = DeliveryPlan.objects.filter(driver=user, date=today, is_completed=False).first()

    if not plan:
        # Check if there's any incomplete plan from the past
        past_plan = DeliveryPlan.objects.filter(
            driver=user,
            date__lt=today,
            is_completed=False
        ).order_by('-date').first()

        if past_plan:
            messages.warning(
                request,
                _("You have an incomplete delivery plan from %(date)s.") % {
                    'date': past_plan.date.strftime('%d/%m/%Y')
                }
            )
            plan = past_plan

    # Get all stops for this plan
    stops = plan.stops.all().order_by('position') if plan else []

    # Count completed stops
    completed_count = sum(1 for stop in stops if stop.status == 'COMPLETED')
    total_count = len(stops)

    context = {
        'plan': plan,
        'stops': stops,
        'completed_count': completed_count,
        'total_count': total_count,
        'progress_percentage': (completed_count / total_count * 100) if total_count > 0 else 0,
    }

    return render(request, 'delivery/driver_today.html', context)

@login_required
def driver_history(request):
    """
    Show delivery history for a driver
    """
    user = request.user

    # Only drivers can access this view
    if not user.is_driver:
        messages.error(request, _("You don't have permission to access driver views."))
        return redirect('users:dashboard')

    # Get all completed delivery plans
    plans = DeliveryPlan.objects.filter(driver=user, is_completed=True).order_by('-date')

    context = {
        'plans': plans,
    }

    return render(request, 'delivery/driver_history.html', context)

# API endpoints

@login_required
def api_optimize_route(request):
    """
    API endpoint for route optimization
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})

    plan_id = request.POST.get('plan_id')

    if not plan_id:
        return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})

    user = request.user

    # Only suppliers and drivers can optimize routes via API
    if not (user.is_supplier or user.is_driver):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})

    try:
        # Get the delivery plan
        if user.is_supplier:
            plan = get_object_or_404(DeliveryPlan, id=plan_id, supplier__admin=user, is_completed=False)
        else:  # Driver
            plan = get_object_or_404(DeliveryPlan, id=plan_id, driver=user, is_completed=False)

        # Check if plan has stops
        if not plan.stops.exists():
            return JsonResponse({'status': 'error', 'message': 'Cannot optimize an empty delivery plan'})

        # Get the optimizer
        optimizer = get_optimizer()

        # Prepare the starting point (warehouse)
        start_point = {
            'lat': float(plan.warehouse_latitude or plan.supplier.latitude or 41.3275),  # Default to Tirana
            'lng': float(plan.warehouse_longitude or plan.supplier.longitude or 19.8187)
        }

        # Prepare the stops
        stops = []
        for stop in plan.stops.all().select_related('shop'):
            stops.append({
                'id': stop.id,
                'lat': float(stop.shop.latitude or 41.3275),  # Default to Tirana
                'lng': float(stop.shop.longitude or 19.8187),
                'priority': stop.priority,
                'time_window_start': stop.time_window_start.strftime('%H:%M') if stop.time_window_start else None,
                'time_window_end': stop.time_window_end.strftime('%H:%M') if stop.time_window_end else None
            })

        # Optimize the route
        result = optimizer.optimize_route(start_point, stops, return_to_start=True)

        # Update the stops with the optimized route
        for i, route_stop in enumerate(result['route']):
            stop = DeliveryStop.objects.get(id=route_stop['stop_id'])
            stop.position = i + 1

            # If the API returned distance and duration, update them
            if 'distance' in route_stop:
                stop.distance_from_previous = Decimal(str(route_stop['distance'] / 1000))  # Convert to km

            # If the API returned arrival times, update them
            if 'arrival_time' in route_stop:
                from datetime import datetime
                arrival_time = datetime.fromtimestamp(route_stop['arrival_time'] / 1000)  # Convert from milliseconds
                stop.estimated_arrival_time = arrival_time.time()

            stop.save()

        # Update the plan with the total distance and duration
        plan.total_distance = Decimal(str(result['total_distance']))
        plan.total_duration = Decimal(str(result['total_time']))
        plan.save()

        # Return updated stop order
        updated_stops = []
        for stop in plan.stops.all().order_by('position'):
            updated_stops.append({
                'id': stop.id,
                'position': stop.position,
                'shop_name': stop.shop.name,
                'order_id': stop.order.id,
                'estimated_arrival': stop.estimated_arrival_time.strftime('%H:%M') if stop.estimated_arrival_time else None,
                'distance': float(stop.distance_from_previous) if stop.distance_from_previous else 0
            })

        return JsonResponse({
            'status': 'success',
            'message': 'Route optimized successfully',
            'stops': updated_stops,
            'total_distance': float(plan.total_distance),
            'total_duration': float(plan.total_duration)
        })

    except Exception as e:
        logger.exception(f"Error in API route optimization: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error optimizing route: {str(e)}'
        })

@login_required
def api_stop_status_update(request):
    """
    API endpoint for updating stop status
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})

    stop_id = request.POST.get('stop_id')
    new_status = request.POST.get('status')

    if not stop_id or not new_status:
        return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})

    user = request.user

    try:
        stop = DeliveryStop.objects.get(id=stop_id)
        plan = stop.delivery_plan
    except DeliveryStop.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Delivery stop not found'})

    # Access control based on user type
    if user.is_supplier:
        if plan.supplier.admin != user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
    elif user.is_driver:
        if plan.driver != user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})

    # Check if status is valid
    valid_statuses = [status[0] for status in DeliveryStop.STOP_STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'})

    # Update stop status
    stop.status = new_status

    # Set actual arrival time if status is ARRIVED and not already set
    if stop.status == 'ARRIVED' and not stop.actual_arrival_time:
        stop.actual_arrival_time = timezone.now().time()

    stop.save()

    # Update order status if stop is completed
    if stop.status == 'COMPLETED' and stop.order.status in ['READY', 'DELIVERING']:
        stop.order.status = 'DELIVERED'
        stop.order.save()

        # Send notification for order status change
        from notifications.tasks import send_order_status_notification
        send_order_status_notification.delay(stop.order.id, 'DELIVERING', 'DELIVERED')

    return JsonResponse({'status': 'success', 'message': 'Stop status updated successfully'})
