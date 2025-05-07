from celery import shared_task
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Notification
from users.models import User
from orders.models import Order

@shared_task
def send_order_status_notification(order_id, old_status, new_status):
    """
    Send a notification to the shop owner when an order status changes
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # Create a notification for the shop owner
        if order.shop and order.shop.admin:
            title = _("Order #%(order_id)s Status Update") % {'order_id': order.id}
            message = _("Your order #%(order_id)s from %(supplier)s has been updated from '%(old_status)s' to '%(new_status)s'.") % {
                'order_id': order.id,
                'supplier': order.supplier.name,
                'old_status': dict(Order.ORDER_STATUS_CHOICES).get(old_status, old_status),
                'new_status': dict(Order.ORDER_STATUS_CHOICES).get(new_status, new_status)
            }
            
            Notification.objects.create(
                recipient=order.shop.admin,
                type='ORDER_STATUS',
                title=title,
                message=message,
                order=order
            )
            
        # Create a notification for the supplier
        if order.supplier and order.supplier.admin and old_status == 'DRAFT' and new_status == 'SUBMITTED':
            title = _("New Order #%(order_id)s Received") % {'order_id': order.id}
            message = _("You have received a new order #%(order_id)s from %(shop)s.") % {
                'order_id': order.id,
                'shop': order.shop.name
            }
            
            Notification.objects.create(
                recipient=order.supplier.admin,
                type='NEW_ORDER',
                title=title,
                message=message,
                order=order
            )
            
        return True
    except Order.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error sending order status notification: {e}")
        return False

@shared_task
def send_delivery_notification(delivery_plan_id, driver_id=None):
    """
    Send a notification to the driver when assigned to a delivery plan
    """
    from delivery.models import DeliveryPlan
    
    try:
        delivery_plan = DeliveryPlan.objects.get(id=delivery_plan_id)
        
        # If a specific driver is provided, use that one
        driver = None
        if driver_id:
            try:
                driver = User.objects.get(id=driver_id, user_type='DRIVER')
            except User.DoesNotExist:
                pass
        else:
            driver = delivery_plan.driver
        
        if driver:
            title = _("New Delivery Assignment for %(date)s") % {'date': delivery_plan.date.strftime('%d/%m/%Y')}
            message = _("You have been assigned to a delivery plan for %(supplier)s on %(date)s with %(stops)s stops.") % {
                'supplier': delivery_plan.supplier.name,
                'date': delivery_plan.date.strftime('%d/%m/%Y'),
                'stops': delivery_plan.stops.count()
            }
            
            Notification.objects.create(
                recipient=driver,
                type='DELIVERY_UPDATE',
                title=title,
                message=message,
                delivery_plan=delivery_plan
            )
            
        return True
    except DeliveryPlan.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error sending delivery notification: {e}")
        return False

@shared_task
def cleanup_old_notifications():
    """
    Remove notifications older than 30 days that have been read
    """
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    deleted_count = Notification.objects.filter(
        created_at__lt=thirty_days_ago,
        is_read=True
    ).delete()[0]
    
    return f"Deleted {deleted_count} old notifications."

@shared_task
def send_system_notification(user_ids, title, message):
    """
    Send a system notification to multiple users
    """
    try:
        users = User.objects.filter(id__in=user_ids)
        notifications = []
        
        for user in users:
            notifications.append(
                Notification(
                    recipient=user,
                    type='SYSTEM',
                    title=title,
                    message=message
                )
            )
        
        if notifications:
            Notification.objects.bulk_create(notifications)
            
        return f"Sent {len(notifications)} system notifications."
    except Exception as e:
        print(f"Error sending system notifications: {e}")
        return False
