"""
MAS Investment - Products Views
Shop, Product Detail, Cart, Wishlist
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.conf import settings

from .models import Product, Category, Wishlist, ProductReview, ProductImage
from apps.orders.models import Cart, CartItem


def home_view(request):
    featured_products = Product.objects.filter(
        status=Product.STATUS_ACTIVE, is_featured=True
    ).select_related('vendor').prefetch_related('images')[:8]
    
    new_arrivals = Product.objects.filter(
        status=Product.STATUS_ACTIVE
    ).select_related('vendor').prefetch_related('images').order_by('-created_at')[:8]
    
    categories = Category.objects.filter(is_active=True, parent=None)[:8]
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
    }
    return render(request, 'customer/home.html', context)


def shop_view(request):
    products = Product.objects.filter(
        status=Product.STATUS_ACTIVE
    ).select_related('vendor', 'category').prefetch_related('images')

    # Filters
    search = request.GET.get('search', '').strip()
    category_slug = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '-created_at')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(vendor__business_name__icontains=search)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    sort_options = {
        '-created_at': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'name': 'name',
        'rating': '-rating',
        'popular': '-total_sold',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'selected_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'total_products': paginator.count,
    }
    return render(request, 'customer/shop.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('vendor', 'category').prefetch_related('images', 'reviews'),
        slug=slug,
        status=Product.STATUS_ACTIVE
    )
    product.views += 1
    product.save(update_fields=['views'])

    related_products = Product.objects.filter(
        category=product.category,
        status=Product.STATUS_ACTIVE
    ).exclude(pk=product.pk)[:4]

    reviews = product.reviews.filter(is_approved=True).select_related('user')
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'customer/product_detail.html', context)


# ─── CART VIEWS ─────────────────────────────────────────────────────────────────

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product__vendor').prefetch_related('product__images')
    context = {'cart': cart, 'items': items}
    return render(request, 'customer/cart.html', context)


@login_required
@require_POST
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=Product.STATUS_ACTIVE)
    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        quantity = 1
    if quantity > product.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Only {product.stock} items in stock.'})
        messages.error(request, f'Only {product.stock} items available.')
        return redirect('products:product_detail', slug=product.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity, 'price_at_add': product.price}
    )

    if not created:
        new_qty = cart_item.quantity + quantity
        if new_qty > product.stock:
            new_qty = product.stock
        cart_item.quantity = new_qty
        cart_item.price_at_add = product.price
        cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart.',
            'cart_count': cart.total_items,
        })

    messages.success(request, f'"{product.name}" added to cart!')
    return redirect('products:cart')


@login_required
@require_POST
def update_cart_view(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    action = request.POST.get('action')
    quantity = request.POST.get('quantity')

    if action == 'remove' or (quantity and int(quantity) == 0):
        item.delete()
        messages.success(request, 'Item removed from cart.')
    elif quantity:
        qty = int(quantity)
        if qty > item.product.stock:
            qty = item.product.stock
        item.quantity = qty
        item.save()

    return redirect('products:cart')


@login_required
@require_POST
def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        added = False
    else:
        added = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'product_id': str(product_id)})

    if added:
        messages.success(request, f'"{product.name}" added to wishlist.')
    else:
        messages.info(request, f'"{product.name}" removed from wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'products:shop'))


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product__vendor').prefetch_related('product__images')
    return render(request, 'customer/wishlist.html', {'items': items})
