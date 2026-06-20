from django.urls import path
from .admin_views import *

app_name = 'admin_panel'
urlpatterns = [
    path('', admin_dashboard_view, name='dashboard'),
    path('customers/', admin_customers_view, name='customers'),
    path('vendors/', admin_vendors_view, name='vendors'),
    path('vendors/<uuid:vendor_id>/approve/', admin_approve_vendor_view, name='approve_vendor'),
    path('vendors/<uuid:vendor_id>/reject/', admin_reject_vendor_view, name='reject_vendor'),
    path('riders/', admin_riders_view, name='riders'),
    path('riders/<uuid:rider_id>/approve/', admin_approve_rider_view, name='approve_rider'),
    path('staff/', admin_staff_view, name='staff'),
    path('staff/create/', admin_create_staff_view, name='create_staff'),
    path('orders/', admin_orders_view, name='orders'),
    path('withdrawals/', admin_withdrawals_view, name='withdrawals'),
    path('withdrawals/<uuid:withdrawal_id>/process/', admin_process_withdrawal_view, name='process_withdrawal'),
    path('analytics/', admin_analytics_view, name='analytics'),
]
