"""
MAS Investment - Admin registrations for all models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import User, CustomerProfile
from apps.vendors.models import Vendor, WithdrawalRequest
from apps.riders.models import Rider
from apps.staff.models import StaffProfile
from apps.products.models import Category, Product, ProductImage, Wishlist, ProductReview
from apps.orders.models import Cart, CartItem, Order, OrderItem, PaymentReceipt, DeliveryAssignment
from apps.support.models import SupportTicket, SupportReply
from apps.notifications.models import Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['role', 'is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Role & Status', {'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2')}),
    )


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'status', 'wallet_balance', 'total_orders', 'created_at']
    list_filter = ['status']
    search_fields = ['business_name', 'user__email']
    actions = ['approve_vendors']

    @admin.action(description='Approve selected vendors')
    def approve_vendors(self, request, queryset):
        from django.utils import timezone
        queryset.update(status=Vendor.STATUS_APPROVED, approved_at=timezone.now())


@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'vehicle_type', 'total_deliveries', 'wallet_balance']
    list_filter = ['status', 'vehicle_type']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'category', 'price', 'stock', 'status', 'is_featured', 'total_sold']
    list_filter = ['status', 'is_featured', 'category']
    search_fields = ['name', 'vendor__business_name']
    list_editable = ['status', 'is_featured']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'total_amount', 'payment_method', 'payment_status', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_status']
    search_fields = ['order_number', 'customer__email']
    readonly_fields = ['order_number', 'created_at']


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'reviewed_by', 'uploaded_at', 'reviewed_at']
    list_filter = ['status']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'customer', 'subject', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['ticket_number', 'subject', 'customer__email']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']

# Simple registrations
admin.site.register(CustomerProfile)
admin.site.register(StaffProfile)
admin.site.register(ProductImage)
admin.site.register(Wishlist)
admin.site.register(ProductReview)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(DeliveryAssignment)
admin.site.register(WithdrawalRequest)
admin.site.register(SupportReply)
