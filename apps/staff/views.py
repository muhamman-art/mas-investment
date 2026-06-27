"""
MAS Investment - Staff Views
Payment Verification, Order Management, Support
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from functools import wraps

from apps.orders.models import Order, PaymentReceipt, DeliveryAssignment, OrderItem
from apps.accounts.models import User
from apps.support.models import SupportTicket, SupportReply
from apps.notifications.models import Notification
from apps.riders.models import Rider
from apps.vendors.models import Vendor


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/login/?next={request.path}')
        if request.user.role not in [User.STAFF, User.SUPER_ADMIN]:
            messages.error(request, 'Access denied. Staff only.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def staff_dashboard_view(request):
    pending_receipts = PaymentReceipt.objects.filter(status=PaymentReceipt.STATUS_PENDING).count()
    processing_orders = Order.objects.filter(status=Order.STATUS_PROCESSING).count()
    open_tickets = SupportTicket.objects.filter(status=SupportTicket.STATUS_OPEN).count()
    total_customers = User.objects.filter(role=User.CUSTOMER).count()

    recent_receipts = PaymentReceipt.objects.filter(
        status=PaymentReceipt.STATUS_PENDING
    ).select_related('order__customer').order_by('-uploaded_at')[:5]

    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]

    context = {
        'pending_receipts': pending_receipts,
        'processing_orders': processing_orders,
        'open_tickets': open_tickets,
        'total_customers': total_customers,
        'recent_receipts': recent_receipts,
        'recent_orders': recent_orders,
    }
    return render(request, 'staff/dashboard.html', context)


@staff_required
def receipt_list_view(request):
    status_filter = request.GET.get('status', 'pending')
    receipts = PaymentReceipt.objects.select_related('order__customer', 'reviewed_by')

    if status_filter != 'all':
        receipts = receipts.filter(status=status_filter)

    receipts = receipts.order_by('-uploaded_at')
    paginator = Paginator(receipts, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'pending_count': PaymentReceipt.objects.filter(status='pending').count(),
    }
    return render(request, 'staff/receipts.html', context)


@staff_required
def receipt_detail_view(request, receipt_id):
    receipt = get_object_or_404(
        PaymentReceipt.objects.select_related('order__customer'),
        pk=receipt_id
    )
    return render(request, 'staff/receipt_detail.html', {'receipt': receipt})


@staff_required
def approve_receipt_view(request, receipt_id):
    receipt = get_object_or_404(PaymentReceipt, pk=receipt_id)
    order = receipt.order

    receipt.status = PaymentReceipt.STATUS_APPROVED
    receipt.reviewed_by = request.user
    receipt.reviewed_at = timezone.now()
    receipt.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

    order.status = Order.STATUS_PROCESSING
    order.payment_status = Order.PAYMENT_STATUS_VERIFIED
    order.paid_at = timezone.now()
    order.save(update_fields=['status', 'payment_status', 'paid_at'])

    # Credit each vendor's wallet for their share of this order
    order_items = OrderItem.objects.filter(order=order, vendor_paid=False)
    vendor_totals = order_items.values('vendor').annotate(total=Sum('vendor_amount'))
    for row in vendor_totals:
        vendor = Vendor.objects.get(pk=row['vendor'])
        vendor.wallet_balance += row['total']
        vendor.save(update_fields=['wallet_balance'])
    order_items.update(vendor_paid=True)

    # Notify customer
    Notification.send(
        user=order.customer,
        notification_type=Notification.TYPE_PAYMENT_APPROVED,
        title='Payment Approved!',
        message=f'Your payment for order #{order.order_number} has been approved. We are processing your order.',
        link=f'/customer/orders/{order.id}/',
        icon='bi-check-circle',
        color='success'
    )

    # Notify vendors
    vendor_ids = order.items.values_list('vendor__user', flat=True).distinct()
    vendor_users = User.objects.filter(pk__in=vendor_ids)
    for vendor_user in vendor_users:
        Notification.send(
            user=vendor_user,
            notification_type=Notification.TYPE_NEW_ORDER,
            title='Order Confirmed - Prepare for Shipping',
            message=f'Order #{order.order_number} payment verified. Please prepare the items.',
            link=f'/vendor/orders/{order.id}/',
            icon='bi-box-seam',
            color='primary'
        )

    messages.success(request, f'Payment approved for order #{order.order_number}.')
    return redirect('staff:receipts')


@staff_required
def reject_receipt_view(request, receipt_id):
    receipt = get_object_or_404(PaymentReceipt, pk=receipt_id)

    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip()
        receipt.status = PaymentReceipt.STATUS_REJECTED
        receipt.rejection_reason = reason
        receipt.reviewed_by = request.user
        receipt.reviewed_at = timezone.now()
        receipt.save()

        order = receipt.order
        order.payment_status = Order.PAYMENT_STATUS_FAILED
        order.save(update_fields=['payment_status'])

        Notification.send(
            user=order.customer,
            notification_type=Notification.TYPE_PAYMENT_REJECTED,
            title='Payment Verification Failed',
            message=f'Your receipt for order #{order.order_number} was rejected. Reason: {reason}. Please upload a valid receipt.',
            link=f'/customer/orders/{order.id}/',
            icon='bi-x-circle',
            color='danger'
        )

        messages.warning(request, f'Receipt rejected for order #{order.order_number}.')
        return redirect('staff:receipts')

    return render(request, 'staff/reject_receipt.html', {'receipt': receipt})


@staff_required
def staff_orders_view(request):
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    orders = Order.objects.select_related('customer').prefetch_related('items').order_by('-created_at')

    if status:
        orders = orders.filter(status=status)
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__email__icontains=search)
        )

    paginator = Paginator(orders, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'status': status,
        'search': search,
        'order_statuses': Order.STATUS_CHOICES,
    }
    return render(request, 'staff/orders.html', context)


@staff_required
def assign_rider_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.method == 'POST':
        rider_id = request.POST.get('rider_id')
        rider = get_object_or_404(Rider, pk=rider_id, status=Rider.STATUS_ACTIVE)

        assignment, created = DeliveryAssignment.objects.get_or_create(
            order=order,
            defaults={'rider': rider, 'status': DeliveryAssignment.STATUS_ASSIGNED}
        )
        if not created:
            assignment.rider = rider
            assignment.status = DeliveryAssignment.STATUS_ASSIGNED
            assignment.save()

        order.status = Order.STATUS_ASSIGNED
        order.save(update_fields=['status'])

        Notification.send(
            user=rider.user,
            notification_type=Notification.TYPE_DELIVERY_ASSIGNED,
            title='New Delivery Assigned',
            message=f'You have been assigned order #{order.order_number}.',
            link=f'/rider/deliveries/{assignment.id}/',
            icon='bi-truck',
            color='info'
        )
        Notification.send(
            user=order.customer,
            notification_type=Notification.TYPE_ORDER_SHIPPED,
            title='Order Assigned to Rider',
            message=f'Your order #{order.order_number} has been assigned to a delivery rider.',
            link=f'/customer/orders/{order.id}/',
            icon='bi-truck',
            color='info'
        )

        messages.success(request, f'Rider assigned for order #{order.order_number}.')
        return redirect('staff:orders')

    available_riders = Rider.objects.filter(status=Rider.STATUS_ACTIVE, is_available=True).select_related('user')
    return render(request, 'staff/assign_rider.html', {
        'order': order,
        'available_riders': available_riders,
    })


@staff_required
def staff_tickets_view(request):
    tickets = SupportTicket.objects.select_related('customer', 'assigned_to').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        tickets = tickets.filter(status=status)

    paginator = Paginator(tickets, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'staff/tickets.html', {
        'page_obj': page_obj,
        'status': status,
        'ticket_statuses': SupportTicket.STATUS_CHOICES,
    })


@staff_required
def staff_ticket_detail_view(request, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.prefetch_related('replies__user'),
        pk=ticket_id
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reply':
            message = request.POST.get('message', '').strip()
            if message:
                SupportReply.objects.create(
                    ticket=ticket,
                    user=request.user,
                    message=message,
                    is_staff_reply=True
                )
                if ticket.status == SupportTicket.STATUS_OPEN:
                    ticket.status = SupportTicket.STATUS_IN_PROGRESS
                    ticket.assigned_to = request.user
                    ticket.save(update_fields=['status', 'assigned_to'])

                Notification.send(
                    user=ticket.customer,
                    notification_type=Notification.TYPE_TICKET_REPLY,
                    title='Support Ticket Update',
                    message=f'Staff replied to your ticket: {ticket.subject}',
                    link=f'/customer/support/{ticket.id}/',
                    icon='bi-chat',
                    color='info'
                )
                messages.success(request, 'Reply sent.')
        elif action == 'resolve':
            ticket.status = SupportTicket.STATUS_RESOLVED
            ticket.resolved_at = timezone.now()
            ticket.save(update_fields=['status', 'resolved_at'])
            Notification.send(
                user=ticket.customer,
                notification_type=Notification.TYPE_TICKET_RESOLVED,
                title='Support Ticket Resolved',
                message=f'Your ticket "{ticket.subject}" has been resolved.',
                link=f'/customer/support/{ticket.id}/',
                icon='bi-check-circle',
                color='success'
            )
            messages.success(request, 'Ticket marked as resolved.')
        elif action == 'close':
            ticket.status = SupportTicket.STATUS_CLOSED
            ticket.save(update_fields=['status'])
            messages.info(request, 'Ticket closed.')

        return redirect('staff:ticket_detail', ticket_id=ticket_id)

    return render(request, 'staff/ticket_detail.html', {'ticket': ticket})
