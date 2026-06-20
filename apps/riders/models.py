"""
MAS Investment - Rider Models
"""
import uuid
from django.db import models
from django.conf import settings


class Rider(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_SUSPENDED = 'suspended'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    VEHICLE_BICYCLE = 'bicycle'
    VEHICLE_MOTORCYCLE = 'motorcycle'
    VEHICLE_CAR = 'car'
    VEHICLE_VAN = 'van'

    VEHICLE_CHOICES = [
        (VEHICLE_BICYCLE, 'Bicycle'),
        (VEHICLE_MOTORCYCLE, 'Motorcycle'),
        (VEHICLE_CAR, 'Car'),
        (VEHICLE_VAN, 'Van'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rider_profile'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default=VEHICLE_MOTORCYCLE)
    vehicle_plate = models.CharField(max_length=20, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    id_document = models.FileField(upload_to='rider_docs/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    current_location = models.CharField(max_length=200, blank=True)
    total_deliveries = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    bank_account_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'riders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Rider: {self.user.get_full_name()}"

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE
