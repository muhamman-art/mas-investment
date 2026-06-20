from django.urls import path
from . import views

app_name = 'vendor'
urlpatterns = [
    path('', views.vendor_dashboard_view, name='dashboard'),
    path('products/', views.vendor_products_view, name='products'),
    path('products/add/', views.vendor_add_product_view, name='add_product'),
    path('products/<uuid:product_id>/edit/', views.vendor_edit_product_view, name='edit_product'),
    path('products/<uuid:product_id>/delete/', views.vendor_delete_product_view, name='delete_product'),
    path('orders/', views.vendor_orders_view, name='orders'),
    path('wallet/', views.vendor_wallet_view, name='wallet'),
    path('reports/', views.vendor_sales_report_view, name='reports'),
]
