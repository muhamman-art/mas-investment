def cart_processor(request):
    if request.user.is_authenticated and hasattr(request.user, 'cart'):
        cart = request.user.cart
        return {
            'cart_item_count': cart.total_items,
            'cart_subtotal': cart.subtotal,
        }
    return {
        'cart_item_count': 0,
        'cart_subtotal': 0,
    }
