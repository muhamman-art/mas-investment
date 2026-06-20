from django.urls import path
from apps.support.views import customer_tickets_view, customer_ticket_detail_view, create_ticket_view
from apps.orders.views import order_list_view, order_detail_view, upload_receipt_view
from apps.accounts.views import profile_view
from apps.products.views import wishlist_view

app_name = 'customer'
urlpatterns = [
    path('', lambda r: __import__('django.shortcuts', fromlist=['redirect']).redirect('customer:orders'), name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('orders/', order_list_view, name='orders'),
    path('orders/<uuid:pk>/', order_detail_view, name='order_detail'),
    path('orders/<uuid:order_id>/receipt/', upload_receipt_view, name='upload_receipt'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('support/', customer_tickets_view, name='tickets'),
    path('support/new/', create_ticket_view, name='create_ticket'),
    path('support/<uuid:ticket_id>/', customer_ticket_detail_view, name='ticket_detail'),
]
