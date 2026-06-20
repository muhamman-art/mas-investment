"""
MAS Investment - Accounts Models
Handles all user types: Customer, Vendor, Rider, Staff, Admin
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.SUPER_ADMIN)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    SUPER_ADMIN = 'super_admin'
    STAFF = 'staff'
    VENDOR = 'vendor'
    RIDER = 'rider'
    CUSTOMER = 'customer'

    ROLE_CHOICES = [
        (SUPER_ADMIN, 'Super Admin'),
        (STAFF, 'Staff'),
        (VENDOR, 'Vendor/Supplier'),
        (RIDER, 'Delivery Rider'),
        (CUSTOMER, 'Customer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CUSTOMER)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_customer(self):
        return self.role == self.CUSTOMER

    @property
    def is_vendor(self):
        return self.role == self.VENDOR

    @property
    def is_rider(self):
        return self.role == self.RIDER

    @property
    def is_platform_staff(self):
        return self.role == self.STAFF

    @property
    def is_super_admin(self):
        return self.role == self.SUPER_ADMIN

    def generate_password_reset_token(self):
        self.password_reset_token = uuid.uuid4()
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save(update_fields=['password_reset_token', 'password_reset_expires'])
        return self.password_reset_token

    def is_password_reset_token_valid(self):
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return timezone.now() < self.password_reset_expires


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    date_of_birth = models.DateField(null=True, blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_profiles'

    def __str__(self):
        return f"Profile: {self.user.get_full_name()}"
