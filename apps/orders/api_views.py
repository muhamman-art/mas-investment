"""
MAS Investment - REST API Views for Orders
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Order
from .serializers import CartSerializer, OrderSerializer
from apps.products.models import Product


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_api(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return Response(CartSerializer(cart).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart_api(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    product = get_object_or_404(Product, pk=product_id, status=Product.STATUS_ACTIVE)

    if quantity > product.stock:
        return Response({'error': f'Only {product.stock} in stock'}, status=status.HTTP_400_BAD_REQUEST)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'quantity': quantity, 'price_at_add': product.price}
    )
    if not created:
        item.quantity = min(item.quantity + quantity, product.stock)
        item.save()

    return Response({'message': 'Added to cart', 'cart_count': cart.total_items})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart_api(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    return Response({'message': 'Removed from cart'})


class OrderListAPI(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).prefetch_related('items').order_by('-created_at')


class OrderDetailAPI(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).prefetch_related('items')
