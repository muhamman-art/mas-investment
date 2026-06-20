"""
MAS Investment - Notification Models
"""
import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_ORDER_PLACED = 'order_placed'
    TYPE_PAYMENT_APPROVED = 'payment_approved'
    TYPE_PAYMENT_REJECTED = 'payment_rejected'
    TYPE_ORDER_SHIPPED = 'order_shipped'
    TYPE_ORDER_DELIVERED = 'order_delivered'
    TYPE_ORDER_CANCELLED = 'order_cancelled'
    TYPE_NEW_ORDER = 'new_order'
    TYPE_LOW_STOCK = 'low_stock'
    TYPE_DELIVERY_ASSIGNED = 'delivery_assigned'
    TYPE_VENDOR_REGISTERED = 'vendor_registered'
    TYPE_VENDOR_APPROVED = 'vendor_approved'
    TYPE_TICKET_REPLY = 'ticket_reply'
    TYPE_TICKET_RESOLVED = 'ticket_resolved'
    TYPE_WITHDRAWAL_PROCESSED = 'withdrawal_processed'
    TYPE_LARGE_ORDER = 'large_order'
    TYPE_GENERAL = 'general'

    TYPE_CHOICES = [
        (TYPE_ORDER_PLACED, 'Order Placed'),
        (TYPE_PAYMENT_APPROVED, 'Payment Approved'),
        (TYPE_PAYMENT_REJECTED, 'Payment Rejected'),
        (TYPE_ORDER_SHIPPED, 'Order Shipped'),
        (TYPE_ORDER_DELIVERED, 'Order Delivered'),
        (TYPE_ORDER_CANCELLED, 'Order Cancelled'),
        (TYPE_NEW_ORDER, 'New Order'),
        (TYPE_LOW_STOCK, 'Low Stock Alert'),
        (TYPE_DELIVERY_ASSIGNED, 'Delivery Assigned'),
        (TYPE_VENDOR_REGISTERED, 'Vendor Registered'),
        (TYPE_VENDOR_APPROVED, 'Vendor Approved'),
        (TYPE_TICKET_REPLY, 'Support Ticket Reply'),
        (TYPE_TICKET_RESOLVED, 'Ticket Resolved'),
        (TYPE_WITHDRAWAL_PROCESSED, 'Withdrawal Processed'),
        (TYPE_LARGE_ORDER, 'Large Order Alert'),
        (TYPE_GENERAL, 'General'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    icon = models.CharField(max_length=50, blank=True, default='bi-bell')
    color = models.CharField(max_length=20, blank=True, default='primary')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.user.email}"

    @classmethod
    def send(cls, user, notification_type, title, message, link='', icon='bi-bell', color='primary'):
        """Convenience method to create notifications."""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
            icon=icon,
            color=color
        )

    @classmethod
    def send_bulk(cls, users, notification_type, title, message, link='', icon='bi-bell', color='primary'):
        """Send to multiple users efficiently."""
        notifications = [
            cls(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link,
                icon=icon,
                color=color
            )
            for user in users
        ]
        return cls.objects.bulk_create(notifications)
