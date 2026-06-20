"""
MAS Investment - Admin Panel Views
Full platform management: users, vendors, riders, orders, analytics
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from functools import wraps
from datetime import timedelta

from apps.accounts.models import User, CustomerProfile
from apps.vendors.models import Vendor, WithdrawalRequest
from apps.riders.models import Rider
from apps.staff.models import StaffProfile
from apps.products.models import Product, Category
from apps.orders.models import Order, PaymentReceipt
from apps.support.models import SupportTicket
from apps.notifications.models import Notification


def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/login/?next={request.path}')
        if request.user.role != User.SUPER_ADMIN:
            messages.error(request, 'Access denied. Super Admin only.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


@superadmin_required
def admin_dashboard_view(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Cards
    total_revenue = Order.objects.filter(
        payment_status=Order.PAYMENT_STATUS_VERIFIED
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_orders = Order.objects.count()
    total_customers = User.objects.filter(role=User.CUSTOMER).count()
    total_vendors = Vendor.objects.count()
    total_riders = Rider.objects.count()
    pending_payments = PaymentReceipt.objects.filter(status=PaymentReceipt.STATUS_PENDING).count()
    pending_deliveries = Order.objects.filter(
        status__in=[Order.STATUS_PROCESSING, Order.STATUS_READY]
    ).count()

    # Monthly data for charts (last 30 days by day)
    from django.db.models.functions import TruncDate
    daily_orders = (
        Order.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'), revenue=Sum('total_amount'))
        .order_by('date')
    )

    chart_labels = [str(d['date']) for d in daily_orders]
    chart_orders = [d['count'] for d in daily_orders]
    chart_revenue = [float(d['revenue'] or 0) for d in daily_orders]

    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    recent_vendors = Vendor.objects.filter(status=Vendor.STATUS_PENDING).select_related('user')[:5]
    open_tickets = SupportTicket.objects.filter(status=SupportTicket.STATUS_OPEN).count()

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'total_riders': total_riders,
        'pending_payments': pending_payments,
        'pending_deliveries': pending_deliveries,
        'open_tickets': open_tickets,
        'chart_labels': chart_labels,
        'chart_orders': chart_orders,
        'chart_revenue': chart_revenue,
        'recent_orders': recent_orders,
        'recent_vendors': recent_vendors,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── USER MANAGEMENT ─────────────────────────────────────────────────────────────

@superadmin_required
def admin_customers_view(request):
    customers = User.objects.filter(role=User.CUSTOMER).select_related('customer_profile')
    search = request.GET.get('search', '')
    if search:
        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    paginator = Paginator(customers.order_by('-date_joined'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/customers.html', {'page_obj': page_obj, 'search': search})


@superadmin_required
def admin_vendors_view(request):
    vendors = Vendor.objects.select_related('user').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        vendors = vendors.filter(status=status)
    paginator = Paginator(vendors, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/vendors.html', {
        'page_obj': page_obj,
        'status': status,
        'vendor_statuses': Vendor.STATUS_CHOICES,
    })


@superadmin_required
def admin_approve_vendor_view(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    vendor.status = Vendor.STATUS_APPROVED
    vendor.approved_at = timezone.now()
    vendor.save(update_fields=['status', 'approved_at'])
    Notification.send(
        user=vendor.user,
        notification_type=Notification.TYPE_VENDOR_APPROVED,
        title='Vendor Account Approved!',
        message=f'Congratulations! Your vendor account "{vendor.business_name}" has been approved. Start adding products!',
        link='/vendor/',
        icon='bi-check-circle',
        color='success'
    )
    messages.success(request, f'Vendor "{vendor.business_name}" approved.')
    return redirect('admin_panel:vendors')


@superadmin_required
def admin_reject_vendor_view(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if request.method == 'POST':
        vendor.status = Vendor.STATUS_REJECTED
        vendor.save(update_fields=['status'])
        messages.warning(request, f'Vendor "{vendor.business_name}" rejected.')
        return redirect('admin_panel:vendors')
    return render(request, 'admin_panel/confirm_action.html', {
        'title': 'Reject Vendor',
        'message': f'Are you sure you want to reject "{vendor.business_name}"?',
    })


@superadmin_required
def admin_riders_view(request):
    riders = Rider.objects.select_related('user').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        riders = riders.filter(status=status)
    paginator = Paginator(riders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/riders.html', {
        'page_obj': page_obj,
        'status': status,
        'rider_statuses': Rider.STATUS_CHOICES,
    })


@superadmin_required
def admin_approve_rider_view(request, rider_id):
    rider = get_object_or_404(Rider, pk=rider_id)
    rider.status = Rider.STATUS_ACTIVE
    rider.save(update_fields=['status'])
    messages.success(request, f'Rider "{rider.user.get_full_name()}" approved.')
    return redirect('admin_panel:riders')


@superadmin_required
def admin_staff_view(request):
    staff_users = User.objects.filter(role=User.STAFF).select_related('staff_profile').order_by('-date_joined')
    return render(request, 'admin_panel/staff.html', {'staff_users': staff_users})


@superadmin_required
def admin_create_staff_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        department = request.POST.get('department', StaffProfile.DEPT_OPERATIONS)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already in use.')
            return redirect('admin_panel:create_staff')

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.STAFF,
            is_staff=True,
            is_verified=True,
        )
        StaffProfile.objects.create(
            user=user,
            department=department,
            can_verify_payments=request.POST.get('can_verify_payments') == 'on',
            can_manage_orders=request.POST.get('can_manage_orders') == 'on',
            can_manage_customers=request.POST.get('can_manage_customers') == 'on',
        )
        messages.success(request, f'Staff account created for {user.get_full_name()}.')
        return redirect('admin_panel:staff')

    return render(request, 'admin_panel/create_staff.html', {
        'departments': StaffProfile.DEPT_CHOICES
    })


@superadmin_required
def admin_orders_view(request):
    orders = Order.objects.select_related('customer').order_by('-created_at')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    if status:
        orders = orders.filter(status=status)
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__email__icontains=search)
        )
    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/orders.html', {
        'page_obj': page_obj,
        'status': status,
        'search': search,
        'order_statuses': Order.STATUS_CHOICES,
    })


@superadmin_required
def admin_withdrawals_view(request):
    withdrawals = WithdrawalRequest.objects.select_related('vendor__user').order_by('-created_at')
    status = request.GET.get('status', 'pending')
    if status != 'all':
        withdrawals = withdrawals.filter(status=status)
    paginator = Paginator(withdrawals, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/withdrawals.html', {
        'page_obj': page_obj,
        'status': status,
    })


@superadmin_required
def admin_process_withdrawal_view(request, withdrawal_id):
    withdrawal = get_object_or_404(WithdrawalRequest, pk=withdrawal_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            if withdrawal.amount > withdrawal.vendor.wallet_balance:
                messages.error(request, 'Vendor has insufficient balance.')
                return redirect('admin_panel:withdrawals')
            withdrawal.status = WithdrawalRequest.STATUS_APPROVED
            withdrawal.vendor.wallet_balance -= withdrawal.amount
            withdrawal.vendor.save(update_fields=['wallet_balance'])
        elif action == 'reject':
            withdrawal.status = WithdrawalRequest.STATUS_REJECTED
            withdrawal.admin_notes = request.POST.get('notes', '')
        withdrawal.processed_by = request.user
        withdrawal.processed_at = timezone.now()
        withdrawal.save()
        Notification.send(
            user=withdrawal.vendor.user,
            notification_type=Notification.TYPE_WITHDRAWAL_PROCESSED,
            title=f'Withdrawal {withdrawal.get_status_display()}',
            message=f'Your withdrawal request of ₦{withdrawal.amount:,.2f} has been {withdrawal.status}.',
            link='/vendor/wallet/',
            icon='bi-wallet',
            color='success' if action == 'approve' else 'danger'
        )
        messages.success(request, f'Withdrawal {withdrawal.status}.')
    return redirect('admin_panel:withdrawals')


@superadmin_required
def admin_analytics_view(request):
    from django.db.models.functions import TruncMonth
    monthly = (
        Order.objects
        .filter(payment_status=Order.PAYMENT_STATUS_VERIFIED)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(revenue=Sum('total_amount'), count=Count('id'))
        .order_by('month')
    )
    top_products = Product.objects.order_by('-total_sold')[:10]
    top_vendors = Vendor.objects.order_by('-total_sales')[:10]

    context = {
        'monthly': monthly,
        'top_products': top_products,
        'top_vendors': top_vendors,
    }
    return render(request, 'admin_panel/analytics.html', context)
