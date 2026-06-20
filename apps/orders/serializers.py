from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, PaymentReceipt, DeliveryAssignment
from apps.products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_at_add', 'total_price']
        read_only_fields = ['price_at_add']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal', 'total_items']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_price', 'quantity', 'subtotal',
                  'vendor_amount', 'commission_amount']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer_name', 'customer_email',
                  'customer_phone', 'recipient_same_as_customer',
                  'recipient_name', 'recipient_phone', 'recipient_address',
                  'delivery_city', 'delivery_state', 'payment_method',
                  'payment_status', 'payment_status_display',
                  'subtotal', 'delivery_fee', 'total_amount',
                  'status', 'status_display', 'notes', 'items',
                  'created_at', 'paid_at', 'delivered_at']
        read_only_fields = ['order_number', 'created_at']


class PaymentReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = ['id', 'receipt_image', 'status', 'uploaded_at', 'reviewed_at']
        read_only_fields = ['status', 'uploaded_at', 'reviewed_at']
