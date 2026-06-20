from django.urls import path
from . import api_views

urlpatterns = [
    path('cart/', api_views.cart_api, name='api_cart'),
    path('cart/add/', api_views.add_to_cart_api, name='api_add_to_cart'),
    path('cart/remove/<uuid:item_id>/', api_views.remove_from_cart_api, name='api_remove_from_cart'),
    path('', api_views.OrderListAPI.as_view(), name='api_orders'),
    path('<uuid:pk>/', api_views.OrderDetailAPI.as_view(), name='api_order_detail'),
]
