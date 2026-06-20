"""
MAS Investment - Staff Models
"""
import uuid
from django.db import models
from django.conf import settings


class StaffProfile(models.Model):
    DEPT_OPERATIONS = 'operations'
    DEPT_SUPPORT = 'support'
    DEPT_FINANCE = 'finance'
    DEPT_LOGISTICS = 'logistics'

    DEPT_CHOICES = [
        (DEPT_OPERATIONS, 'Operations'),
        (DEPT_SUPPORT, 'Customer Support'),
        (DEPT_FINANCE, 'Finance'),
        (DEPT_LOGISTICS, 'Logistics'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    department = models.CharField(max_length=20, choices=DEPT_CHOICES, default=DEPT_OPERATIONS)
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    can_verify_payments = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=True)
    can_manage_customers = models.BooleanField(default=False)
    can_manage_vendors = models.BooleanField(default=False)
    can_manage_riders = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_profiles'

    def __str__(self):
        return f"Staff: {self.user.get_full_name()} ({self.department})"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            import random, string
            self.employee_id = 'EMP-' + ''.join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)
