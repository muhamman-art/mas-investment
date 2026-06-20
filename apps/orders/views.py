"""
MAS Investment - Orders Views
Checkout, Order Tracking, Order History
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Cart, CartItem, Order, OrderItem, PaymentReceipt, DeliveryAssignment
from apps.products.models import Product
from apps.notifications.models import Notification
from apps.accounts.models import User


ALLOWED_RECEIPT_EXTENSIONS = ['jpg', 'jpeg', 'png', 'pdf']
MAX_RECEIPT_SIZE = 10 * 1024 * 1024  # 10MB


@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('product__vendor').prefetch_related('product__images')

    if not items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:cart')

    # Check stock
    for item in items:
        if item.product.stock < item.quantity:
            messages.error(request, f'Sorry, only {item.product.stock} of "{item.product.name}" available.')
            return redirect('products:cart')

    if request.method == 'POST':
        return _process_checkout(request, cart, items)

    user = request.user
    context = {
        'cart': cart,
        'items': items,
        'user': user,
    }
    return render(request, 'customer/checkout.html', context)


def _process_checkout(request, cart, items):
    user = request.user
    payment_method = request.POST.get('payment_method', Order.PAYMENT_BANK_TRANSFER)
    recipient_same = request.POST.get('recipient_same_as_customer') == 'on'

    # Build order
    subtotal = cart.subtotal
    delivery_fee = 0
    total = subtotal + delivery_fee

    order = Order.objects.create(
        customer=user,
        customer_name=request.POST.get('customer_name', user.get_full_name()),
        customer_email=request.POST.get('customer_email', user.email),
        customer_phone=request.POST.get('customer_phone', user.phone),
        recipient_same_as_customer=recipient_same,
        recipient_name='' if recipient_same else request.POST.get('recipient_name', ''),
        recipient_phone='' if recipient_same else request.POST.get('recipient_phone', ''),
        recipient_address=request.POST.get('recipient_address', ''),
        delivery_city=request.POST.get('delivery_city', ''),
        delivery_state=request.POST.get('delivery_state', ''),
        payment_method=payment_method,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total,
        notes=request.POST.get('notes', ''),
    )

    # Create order items & update stock
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            vendor=item.product.vendor,
            product_name=item.product.name,
            product_price=item.price_at_add,
            quantity=item.quantity,
        )
        item.product.stock -= item.quantity
        item.product.total_sold += item.quantity
        item.product.save(update_fields=['stock', 'total_sold'])

    # Handle receipt upload for bank transfer
    if payment_method == Order.PAYMENT_BANK_TRANSFER:
        receipt_file = request.FILES.get('receipt')
        if receipt_file:
            ext = receipt_file.name.split('.')[-1].lower()
            if ext not in ALLOWED_RECEIPT_EXTENSIONS:
                order.delete()
                messages.error(request, f'Invalid file type. Allowed: {", ".join(ALLOWED_RECEIPT_EXTENSIONS)}')
                return redirect('orders:checkout')
            if receipt_file.size > MAX_RECEIPT_SIZE:
                order.delete()
                messages.error(request, 'File too large. Maximum 10MB allowed.')
                return redirect('orders:checkout')

            PaymentReceipt.objects.create(order=order, receipt_image=receipt_file)
            order.status = Order.STATUS_AWAITING_VERIFICATION
            order.payment_status = Order.PAYMENT_STATUS_AWAITING
            order.save(update_fields=['status', 'payment_status'])
        else:
            order.status = Order.STATUS_PENDING
            order.save(update_fields=['status'])
    else:
        # Cash on delivery - goes straight to processing
        order.status = Order.STATUS_PROCESSING
        order.payment_status = Order.PAYMENT_STATUS_PENDING
        order.save(update_fields=['status', 'payment_status'])

    # Clear cart
    cart.items.all().delete()

    # Notify customer
    Notification.send(
        user=user,
        notification_type=Notification.TYPE_ORDER_PLACED,
        title='Order Placed Successfully',
        message=f'Your order #{order.order_number} has been placed.',
        link=f'/customer/orders/{order.id}/',
        icon='bi-bag-check',
        color='success'
    )

    # Notify vendors
    vendor_users = set(item.product.vendor.user for item in items)
    for vendor_user in vendor_users:
        Notification.send(
            user=vendor_user,
            notification_type=Notification.TYPE_NEW_ORDER,
            title='New Order Received',
            message=f'Order #{order.order_number} has been placed.',
            link=f'/vendor/orders/{order.id}/',
            icon='bi-box',
            color='info'
        )

    # Notify admins for large orders
    if total >= 100000:
        admins = User.objects.filter(role=User.SUPER_ADMIN)
        for admin in admins:
            Notification.send(
                user=admin,
                notification_type=Notification.TYPE_LARGE_ORDER,
                title='Large Order Alert',
                message=f'Order #{order.order_number} worth ₦{total:,.2f} placed.',
                link=f'/admin-panel/orders/{order.id}/',
                icon='bi-exclamation-triangle',
                color='warning'
            )

    messages.success(request, f'Order #{order.order_number} placed successfully!')
    return redirect('orders:order_confirmation', pk=order.pk)


@login_required
def order_confirmation_view(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, 'customer/order_confirmation.html', {'order': order})


@login_required
def order_list_view(request):
    orders = Order.objects.filter(
        customer=request.user
    ).prefetch_related('items').order_by('-created_at')

    paginator = __import__('django.core.paginator', fromlist=['Paginator']).Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'customer/orders.html', {'page_obj': page_obj})


@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product', 'items__vendor'),
        pk=pk,
        customer=request.user
    )
    return render(request, 'customer/order_detail.html', {'order': order})


@login_required
@require_POST
def upload_receipt_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)

    if order.payment_method != Order.PAYMENT_BANK_TRANSFER:
        messages.error(request, 'Receipt upload only for bank transfers.')
        return redirect('orders:order_detail', pk=order_id)

    if hasattr(order, 'payment_receipt') and order.payment_receipt.status == PaymentReceipt.STATUS_APPROVED:
        messages.error(request, 'Payment already approved.')
        return redirect('orders:order_detail', pk=order_id)

    receipt_file = request.FILES.get('receipt')
    if not receipt_file:
        messages.error(request, 'No file uploaded.')
        return redirect('orders:order_detail', pk=order_id)

    ext = receipt_file.name.split('.')[-1].lower()
    if ext not in ALLOWED_RECEIPT_EXTENSIONS:
        messages.error(request, f'Invalid file type. Allowed: {", ".join(ALLOWED_RECEIPT_EXTENSIONS)}')
        return redirect('orders:order_detail', pk=order_id)

    if receipt_file.size > MAX_RECEIPT_SIZE:
        messages.error(request, 'File too large. Max 10MB.')
        return redirect('orders:order_detail', pk=order_id)

    if hasattr(order, 'payment_receipt'):
        order.payment_receipt.receipt_image = receipt_file
        order.payment_receipt.status = PaymentReceipt.STATUS_PENDING
        order.payment_receipt.save()
    else:
        PaymentReceipt.objects.create(order=order, receipt_image=receipt_file)

    order.status = Order.STATUS_AWAITING_VERIFICATION
    order.payment_status = Order.PAYMENT_STATUS_AWAITING
    order.save(update_fields=['status', 'payment_status'])

    messages.success(request, 'Receipt uploaded. Awaiting verification.')
    return redirect('orders:order_detail', pk=order_id)
