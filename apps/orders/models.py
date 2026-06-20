"""
MAS Investment - Orders Models
Cart, Orders, Payment Receipts, Delivery Assignments
"""
import uuid
import os
from django.db import models
from django.conf import settings


def receipt_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('receipts', str(instance.order.id), new_filename)


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f"Cart of {self.user.email}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    price_at_add = models.DecimalField(max_digits=12, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def total_price(self):
        return self.price_at_add * self.quantity


class Order(models.Model):
    # Status flow
    STATUS_PENDING = 'pending'
    STATUS_AWAITING_VERIFICATION = 'awaiting_verification'
    STATUS_PAID = 'paid'
    STATUS_PROCESSING = 'processing'
    STATUS_READY = 'ready'
    STATUS_ASSIGNED = 'assigned'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_AWAITING_VERIFICATION, 'Awaiting Payment Verification'),
        (STATUS_PAID, 'Paid'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_READY, 'Ready for Pickup'),
        (STATUS_ASSIGNED, 'Rider Assigned'),
        (STATUS_PICKED_UP, 'Picked Up'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    PAYMENT_BANK_TRANSFER = 'bank_transfer'
    PAYMENT_CASH = 'cash_on_delivery'

    PAYMENT_CHOICES = [
        (PAYMENT_BANK_TRANSFER, 'Bank Transfer'),
        (PAYMENT_CASH, 'Cash on Delivery'),
    ]

    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_AWAITING = 'awaiting_verification'
    PAYMENT_STATUS_VERIFIED = 'verified'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_AWAITING, 'Awaiting Verification'),
        (PAYMENT_STATUS_VERIFIED, 'Verified'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
        (PAYMENT_STATUS_REFUNDED, 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    # Customer details
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    # Recipient details
    recipient_same_as_customer = models.BooleanField(default=True)
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_state = models.CharField(max_length=100, blank=True)

    # Payment
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default=PAYMENT_BANK_TRANSFER)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)

    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def _generate_order_number(self):
        import random, string
        from django.utils import timezone
        prefix = 'MAS'
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{date_part}-{random_part}"

    @property
    def effective_recipient_name(self):
        return self.customer_name if self.recipient_same_as_customer else self.recipient_name

    @property
    def effective_recipient_phone(self):
        return self.customer_phone if self.recipient_same_as_customer else self.recipient_phone

    @property
    def effective_recipient_address(self):
        return self.recipient_address


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='order_items')
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=300)
    product_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    vendor_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_paid = models.BooleanField(default=False)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in {self.order.order_number}"

    def save(self, *args, **kwargs):
        self.subtotal = self.product_price * self.quantity
        commission_rate = self.vendor.commission_rate / 100
        self.commission_amount = self.subtotal * commission_rate
        self.vendor_amount = self.subtotal - self.commission_amount
        super().save(*args, **kwargs)


class PaymentReceipt(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment_receipt')
    receipt_image = models.FileField(upload_to=receipt_upload_path)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_receipts'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment_receipts'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Receipt for {self.order.order_number}"

    @property
    def file_extension(self):
        name = self.receipt_image.name
        return name.split('.')[-1].lower() if name else ''

    @property
    def is_pdf(self):
        return self.file_extension == 'pdf'


class DeliveryAssignment(models.Model):
    STATUS_ASSIGNED = 'assigned'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'

    STATUS_CHOICES = [
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_PICKED_UP, 'Picked Up'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (STATUS_DELIVERED, 'Delivered'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    rider = models.ForeignKey(
        'riders.Rider',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assignments'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_ASSIGNED)
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'delivery_assignments'
        ordering = ['-assigned_at']

    def __str__(self):
        return f"Delivery for {self.order.order_number}"
