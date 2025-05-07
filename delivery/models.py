from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class DeliveryPlan(models.Model):
    """Daily delivery plan for a supplier"""
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='delivery_plans',
        verbose_name=_('Supplier')
    )
    driver = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='delivery_plans',
        verbose_name=_('Driver')
    )
    date = models.DateField(_('Date'))
    notes = models.TextField(_('Notes'), blank=True)
    is_completed = models.BooleanField(_('Completed'), default=False)

    # Route optimization fields
    total_distance = models.DecimalField(_('Total Distance (km)'), max_digits=10, decimal_places=2, default=0)
    total_duration = models.DecimalField(_('Total Duration (min)'), max_digits=10, decimal_places=2, default=0)
    optimize_route = models.BooleanField(_('Optimize Route'), default=True)

    # Warehouse/starting point coordinates
    warehouse_latitude = models.DecimalField(_('Warehouse Latitude'), max_digits=9, decimal_places=6,
                                           null=True, blank=True)
    warehouse_longitude = models.DecimalField(_('Warehouse Longitude'), max_digits=9, decimal_places=6,
                                            null=True, blank=True)

    # Timestamps and metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Delivery Plan')
        verbose_name_plural = _('Delivery Plans')
        unique_together = ('supplier', 'date', 'driver')
        ordering = ['-date']

    def __str__(self):
        return f"{_('Delivery plan for')} {self.supplier.name} {_('on')} {self.date}"

    def get_stop_count(self):
        """Return the number of stops in this plan"""
        return self.stops.count()

    def get_total_orders(self):
        """Return the total value of all orders in this plan"""
        return sum(stop.order.total_amount for stop in self.stops.all())

    def save(self, *args, **kwargs):
        # If warehouse coordinates are not set, use supplier's coordinates
        if not self.warehouse_latitude and hasattr(self.supplier, 'latitude') and self.supplier.latitude:
            self.warehouse_latitude = self.supplier.latitude
            self.warehouse_longitude = self.supplier.longitude
        super().save(*args, **kwargs)

class DeliveryStop(models.Model):
    """Individual stop in a delivery plan"""
    delivery_plan = models.ForeignKey(
        DeliveryPlan,
        on_delete=models.CASCADE,
        related_name='stops',
        verbose_name=_('Delivery Plan')
    )
    shop = models.ForeignKey(
        'shops.Shop',
        on_delete=models.PROTECT,
        verbose_name=_('Shop')
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.PROTECT,
        verbose_name=_('Order'),
        null=True,
        blank=True
    )
    position = models.PositiveIntegerField(_('Position'), default=0)  # For ordering stops
    estimated_arrival_time = models.TimeField(_('Estimated Arrival Time'), null=True, blank=True)
    actual_arrival_time = models.TimeField(_('Actual Arrival Time'), null=True, blank=True)
    notes = models.TextField(_('Notes'), blank=True)

    # Route optimization fields
    distance_from_previous = models.DecimalField(_('Distance from Previous Stop (km)'),
                                               max_digits=10, decimal_places=2, default=0)
    duration_from_previous = models.DecimalField(_('Duration from Previous Stop (min)'),
                                               max_digits=10, decimal_places=2, default=0)
    # Priority (lower number = higher priority)
    priority = models.PositiveSmallIntegerField(_('Priority'), default=5)
    # Time window for delivery
    time_window_start = models.TimeField(_('Time Window Start'), null=True, blank=True)
    time_window_end = models.TimeField(_('Time Window End'), null=True, blank=True)

    STOP_STATUS_CHOICES = (
        ('PENDING', _('Pending')),
        ('ARRIVED', _('Arrived')),
        ('COMPLETED', _('Completed')),
        ('SKIPPED', _('Skipped')),
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STOP_STATUS_CHOICES,
        default='PENDING'
    )

    class Meta:
        verbose_name = _('Delivery Stop')
        verbose_name_plural = _('Delivery Stops')
        ordering = ['position']

    def __str__(self):
        return f"{_('Stop')} {self.position} - {self.shop.name}"

    def get_status_display_class(self):
        """Return CSS class based on status for UI styling"""
        status_classes = {
            'PENDING': 'secondary',
            'ARRIVED': 'warning',
            'COMPLETED': 'success',
            'SKIPPED': 'danger'
        }
        return status_classes.get(self.status, 'secondary')
