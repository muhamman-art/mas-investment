"""
MAS Investment - Rider Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps

from apps.accounts.models import User
from apps.riders.models import Rider
from apps.orders.models import Order, DeliveryAssignment
from apps.notifications.models import Notification


def rider_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/login/?next={request.path}')
        if request.user.role != User.RIDER:
            messages.error(request, 'Access denied. Rider account required.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


@rider_required
def rider_dashboard_view(request):
    rider = get_object_or_404(Rider, user=request.user)
    assignments = DeliveryAssignment.objects.filter(
        rider=rider
    ).select_related('order__customer').order_by('-assigned_at')

    pending = assignments.filter(status=DeliveryAssignment.STATUS_ASSIGNED).count()
    active = assignments.filter(
        status__in=[DeliveryAssignment.STATUS_ACCEPTED, DeliveryAssignment.STATUS_PICKED_UP, DeliveryAssignment.STATUS_OUT_FOR_DELIVERY]
    ).count()
    completed = assignments.filter(status=DeliveryAssignment.STATUS_DELIVERED).count()
    recent = assignments[:10]

    context = {
        'rider': rider,
        'pending': pending,
        'active': active,
        'completed': completed,
        'recent': recent,
        'total_earnings': rider.total_earnings,
    }
    return render(request, 'rider/dashboard.html', context)


@rider_required
def rider_deliveries_view(request):
    rider = get_object_or_404(Rider, user=request.user)
    status = request.GET.get('status', '')
    assignments = DeliveryAssignment.objects.filter(rider=rider).select_related('order__customer')

    if status:
        assignments = assignments.filter(status=status)

    assignments = assignments.order_by('-assigned_at')
    paginator = Paginator(assignments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'rider/deliveries.html', {
        'page_obj': page_obj,
        'rider': rider,
        'status': status,
        'statuses': DeliveryAssignment.STATUS_CHOICES,
    })


@rider_required
def rider_delivery_detail_view(request, assignment_id):
    rider = get_object_or_404(Rider, user=request.user)
    assignment = get_object_or_404(
        DeliveryAssignment.objects.select_related('order__customer'),
        pk=assignment_id,
        rider=rider
    )
    return render(request, 'rider/delivery_detail.html', {
        'assignment': assignment,
        'rider': rider,
    })


@rider_required
def update_delivery_status_view(request, assignment_id):
    rider = get_object_or_404(Rider, user=request.user)
    assignment = get_object_or_404(DeliveryAssignment, pk=assignment_id, rider=rider)
    order = assignment.order

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_transitions = {
            DeliveryAssignment.STATUS_ASSIGNED: [DeliveryAssignment.STATUS_ACCEPTED, DeliveryAssignment.STATUS_REJECTED],
            DeliveryAssignment.STATUS_ACCEPTED: [DeliveryAssignment.STATUS_PICKED_UP],
            DeliveryAssignment.STATUS_PICKED_UP: [DeliveryAssignment.STATUS_OUT_FOR_DELIVERY],
            DeliveryAssignment.STATUS_OUT_FOR_DELIVERY: [DeliveryAssignment.STATUS_DELIVERED],
        }

        if new_status not in valid_transitions.get(assignment.status, []):
            messages.error(request, 'Invalid status transition.')
            return redirect('rider:delivery_detail', assignment_id=assignment_id)

        now = timezone.now()
        assignment.status = new_status

        if new_status == DeliveryAssignment.STATUS_ACCEPTED:
            assignment.accepted_at = now
            order.status = Order.STATUS_PICKED_UP
        elif new_status == DeliveryAssignment.STATUS_REJECTED:
            assignment.rejection_reason = request.POST.get('reason', '')
            order.status = Order.STATUS_PROCESSING
            rider.is_available = True
            rider.save(update_fields=['is_available'])
        elif new_status == DeliveryAssignment.STATUS_PICKED_UP:
            assignment.picked_up_at = now
            order.status = Order.STATUS_PICKED_UP
        elif new_status == DeliveryAssignment.STATUS_OUT_FOR_DELIVERY:
            order.status = Order.STATUS_OUT_FOR_DELIVERY
        elif new_status == DeliveryAssignment.STATUS_DELIVERED:
            assignment.delivered_at = now
            order.status = Order.STATUS_DELIVERED
            order.delivered_at = now
            rider.total_deliveries += 1
            rider.total_earnings += assignment.delivery_fee
            rider.wallet_balance += assignment.delivery_fee
            rider.is_available = True
            rider.save(update_fields=['total_deliveries', 'total_earnings', 'wallet_balance', 'is_available'])

            Notification.send(
                user=order.customer,
                notification_type=Notification.TYPE_ORDER_DELIVERED,
                title='Order Delivered!',
                message=f'Your order #{order.order_number} has been delivered. Enjoy!',
                link=f'/customer/orders/{order.id}/',
                icon='bi-bag-check',
                color='success'
            )

        assignment.save()
        order.save(update_fields=['status', 'delivered_at'])
        messages.success(request, f'Delivery status updated to: {assignment.get_status_display()}')

    return redirect('rider:delivery_detail', assignment_id=assignment_id)


@rider_required
def toggle_availability_view(request):
    rider = get_object_or_404(Rider, user=request.user)
    rider.is_available = not rider.is_available
    rider.save(update_fields=['is_available'])
    status = 'available' if rider.is_available else 'unavailable'
    messages.success(request, f'You are now marked as {status}.')
    return redirect('rider:dashboard')
