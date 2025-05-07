from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse

from .models import Notification
from .forms import NotificationFilterForm

@login_required
def notification_list(request):
    """
    List all notifications for the current user
    """
    # Initialize filter form
    filter_form = NotificationFilterForm(request.GET)
    
    # Base queryset - only show notifications for the current user
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Apply filters if the form is valid
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        # Type filter
        if data.get('type'):
            notifications = notifications.filter(type=data['type'])
        
        # Read status filter
        if data.get('read_status') == 'read':
            notifications = notifications.filter(is_read=True)
        elif data.get('read_status') == 'unread':
            notifications = notifications.filter(is_read=False)
        
        # Date range filters
        if data.get('date_from'):
            notifications = notifications.filter(created_at__date__gte=data['date_from'])
        
        if data.get('date_to'):
            notifications = notifications.filter(created_at__date__lte=data['date_to'])
    
    # Order by created_at (newest first)
    notifications = notifications.order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'filter_form': filter_form,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    
    return render(request, 'notifications/notification_list.html', context)

@login_required
def notification_detail(request, notification_id):
    """
    View details of a notification
    """
    # Get the notification and verify ownership
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # Mark as read if not already
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notifications/notification_detail.html', context)

@login_required
def notification_mark_read(request, notification_id):
    """
    Mark a notification as read
    """
    # Get the notification and verify ownership
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # Mark as read
    notification.is_read = True
    notification.save()
    
    # Determine redirect URL
    redirect_url = request.GET.get('next', 'notifications:notification_list')
    
    messages.success(request, _("Notification marked as read."))
    
    if redirect_url.startswith('http'):
        # Don't allow redirecting to external URLs for security
        redirect_url = 'notifications:notification_list'
    
    return redirect(redirect_url)

@login_required
def notification_mark_all_read(request):
    """
    Mark all notifications as read
    """
    # Update all unread notifications for the current user
    updated_count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).update(is_read=True)
    
    if updated_count > 0:
        messages.success(
            request, 
            _("%(count)s notifications marked as read.") % {'count': updated_count}
        )
    else:
        messages.info(request, _("No unread notifications."))
    
    # Redirect back to the notification list
    return redirect('notifications:notification_list')

@login_required
def notification_clear_all(request):
    """
    Delete all read notifications
    """
    # Delete all read notifications for the current user
    deleted_count, _ = Notification.objects.filter(
        recipient=request.user, 
        is_read=True
    ).delete()
    
    if deleted_count > 0:
        messages.success(
            request, 
            _("%(count)s read notifications cleared.") % {'count': deleted_count}
        )
    else:
        messages.info(request, _("No read notifications to clear."))
    
    # Redirect back to the notification list
    return redirect('notifications:notification_list')

# API endpoints

@login_required
def api_notification_count(request):
    """
    API endpoint for getting the unread notification count
    """
    # Count unread notifications for the current user
    unread_count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    return JsonResponse({
        'count': unread_count,
    })

@login_required
def api_notification_recent(request):
    """
    API endpoint for getting recent notifications
    """
    # Get the 5 most recent notifications for the current user
    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]
    
    # Format the notifications
    notifications_list = []
    for notification in recent_notifications:
        notifications_list.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'is_read': notification.is_read,
            'url': f'/notifications/{notification.id}/',
        })
    
    return JsonResponse({
        'notifications': notifications_list,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })
