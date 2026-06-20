"""
MAS Investment - Vendor Views
Dashboard, Products, Orders, Wallet, Withdrawals
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from functools import wraps

from apps.accounts.models import User
from apps.vendors.models import Vendor, WithdrawalRequest
from apps.products.models import Product, ProductImage, Category
from apps.orders.models import Order, OrderItem
from apps.notifications.models import Notification


def vendor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/login/?next={request.path}')
        if request.user.role != User.VENDOR:
            messages.error(request, 'Access denied. Vendor account required.')
            return redirect('/')
        if not hasattr(request.user, 'vendor_profile'):
            messages.error(request, 'Vendor profile not found.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


@vendor_required
def vendor_dashboard_view(request):
    vendor = request.user.vendor_profile
    products = Product.objects.filter(vendor=vendor)
    orders = OrderItem.objects.filter(vendor=vendor).select_related('order')

    total_revenue = orders.filter(
        order__payment_status=Order.PAYMENT_STATUS_VERIFIED
    ).aggregate(total=Sum('vendor_amount'))['total'] or 0

    total_orders = orders.values('order').distinct().count()
    active_products = products.filter(status=Product.STATUS_ACTIVE).count()
    low_stock = products.filter(stock__lte=5, stock__gt=0).count()

    recent_orders = orders.select_related(
        'order__customer', 'product'
    ).order_by('-order__created_at')[:10]

    context = {
        'vendor': vendor,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'active_products': active_products,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
    }
    return render(request, 'vendor/dashboard.html', context)


@vendor_required
def vendor_products_view(request):
    vendor = request.user.vendor_profile
    products = Product.objects.filter(vendor=vendor).prefetch_related('images').order_by('-created_at')

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    if search:
        products = products.filter(name__icontains=search)
    if status:
        products = products.filter(status=status)

    paginator = Paginator(products, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'vendor': vendor,
        'search': search,
        'status': status,
        'product_statuses': Product.STATUS_CHOICES,
    }
    return render(request, 'vendor/products.html', context)


@vendor_required
def vendor_add_product_view(request):
    vendor = request.user.vendor_profile
    categories = Category.objects.filter(is_active=True)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price')
        stock = request.POST.get('stock', 0)
        category_id = request.POST.get('category')
        compare_price = request.POST.get('compare_price') or None

        if not all([name, description, price]):
            messages.error(request, 'Name, description, and price are required.')
            return render(request, 'vendor/product_form.html', {
                'categories': categories, 'form_data': request.POST
            })

        product = Product.objects.create(
            vendor=vendor,
            name=name,
            description=description,
            short_description=request.POST.get('short_description', ''),
            price=price,
            compare_price=compare_price,
            stock=int(stock),
            category_id=category_id or None,
            sku=request.POST.get('sku', '') or None,
            weight=request.POST.get('weight') or None,
            status=request.POST.get('status', Product.STATUS_ACTIVE),
            is_featured=request.POST.get('is_featured') == 'on',
        )

        # Handle images
        images = request.FILES.getlist('images')
        for i, img in enumerate(images[:5]):  # Max 5 images
            ProductImage.objects.create(
                product=product,
                image=img,
                is_primary=(i == 0),
                order=i
            )

        # Check low stock after creation
        if product.is_low_stock:
            Notification.send(
                user=request.user,
                notification_type=Notification.TYPE_LOW_STOCK,
                title='Low Stock Alert',
                message=f'"{product.name}" has low stock ({product.stock} remaining).',
                link=f'/vendor/products/{product.id}/edit/',
                icon='bi-exclamation-triangle',
                color='warning'
            )

        messages.success(request, f'Product "{product.name}" added successfully!')
        return redirect('vendor:products')

    return render(request, 'vendor/product_form.html', {
        'categories': categories,
        'action': 'Add',
    })


@vendor_required
def vendor_edit_product_view(request, product_id):
    vendor = request.user.vendor_profile
    product = get_object_or_404(Product, pk=product_id, vendor=vendor)
    categories = Category.objects.filter(is_active=True)

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.description = request.POST.get('description', product.description).strip()
        product.short_description = request.POST.get('short_description', '')
        product.price = request.POST.get('price', product.price)
        product.compare_price = request.POST.get('compare_price') or None
        product.stock = int(request.POST.get('stock', product.stock))
        product.category_id = request.POST.get('category') or None
        product.sku = request.POST.get('sku', '') or None
        product.weight = request.POST.get('weight') or None
        product.status = request.POST.get('status', product.status)
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.save()

        new_images = request.FILES.getlist('images')
        for img in new_images[:5]:
            ProductImage.objects.create(
                product=product,
                image=img,
                is_primary=not product.images.filter(is_primary=True).exists()
            )

        # Check low stock
        if product.is_low_stock:
            Notification.send(
                user=request.user,
                notification_type=Notification.TYPE_LOW_STOCK,
                title='Low Stock Alert',
                message=f'"{product.name}" is running low ({product.stock} left).',
                link=f'/vendor/products/{product.id}/edit/',
                icon='bi-exclamation-triangle',
                color='warning'
            )

        messages.success(request, f'Product "{product.name}" updated!')
        return redirect('vendor:products')

    return render(request, 'vendor/product_form.html', {
        'categories': categories,
        'product': product,
        'action': 'Edit',
    })


@vendor_required
def vendor_delete_product_view(request, product_id):
    vendor = request.user.vendor_profile
    product = get_object_or_404(Product, pk=product_id, vendor=vendor)
    if request.method == 'POST':
        name = product.name
        product.status = Product.STATUS_INACTIVE
        product.save(update_fields=['status'])
        messages.success(request, f'Product "{name}" deactivated.')
    return redirect('vendor:products')


@vendor_required
def vendor_orders_view(request):
    vendor = request.user.vendor_profile
    order_items = OrderItem.objects.filter(
        vendor=vendor
    ).select_related('order__customer', 'product').order_by('-order__created_at')

    status = request.GET.get('status', '')
    if status:
        order_items = order_items.filter(order__status=status)

    paginator = Paginator(order_items, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'status': status,
        'order_statuses': Order.STATUS_CHOICES,
    }
    return render(request, 'vendor/orders.html', context)


@vendor_required
def vendor_wallet_view(request):
    vendor = request.user.vendor_profile
    withdrawals = WithdrawalRequest.objects.filter(vendor=vendor).order_by('-created_at')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
            if amount > float(vendor.wallet_balance):
                messages.error(request, f'Insufficient balance. Available: ₦{vendor.wallet_balance:,.2f}')
                return redirect('vendor:wallet')

            WithdrawalRequest.objects.create(
                vendor=vendor,
                amount=amount,
                notes=request.POST.get('notes', '')
            )
            messages.success(request, f'Withdrawal request of ₦{amount:,.2f} submitted.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount.')
        return redirect('vendor:wallet')

    context = {
        'vendor': vendor,
        'withdrawals': withdrawals[:10],
    }
    return render(request, 'vendor/wallet.html', context)


@vendor_required
def vendor_sales_report_view(request):
    vendor = request.user.vendor_profile
    order_items = OrderItem.objects.filter(
        vendor=vendor,
        order__payment_status=Order.PAYMENT_STATUS_VERIFIED
    ).select_related('order', 'product')

    total_revenue = order_items.aggregate(total=Sum('vendor_amount'))['total'] or 0
    total_commission = order_items.aggregate(total=Sum('commission_amount'))['total'] or 0
    total_orders = order_items.values('order').distinct().count()
    total_items_sold = order_items.aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'vendor': vendor,
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'total_orders': total_orders,
        'total_items_sold': total_items_sold,
        'order_items': order_items.order_by('-order__created_at')[:20],
    }
    return render(request, 'vendor/sales_report.html', context)
