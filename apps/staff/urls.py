from django.urls import path
from . import views

app_name = 'staff'
urlpatterns = [
    path('', views.staff_dashboard_view, name='dashboard'),
    path('receipts/', views.receipt_list_view, name='receipts'),
    path('receipts/<uuid:receipt_id>/', views.receipt_detail_view, name='receipt_detail'),
    path('receipts/<uuid:receipt_id>/approve/', views.approve_receipt_view, name='approve_receipt'),
    path('receipts/<uuid:receipt_id>/reject/', views.reject_receipt_view, name='reject_receipt'),
    path('orders/', views.staff_orders_view, name='orders'),
    path('orders/<uuid:order_id>/assign-rider/', views.assign_rider_view, name='assign_rider'),
    path('tickets/', views.staff_tickets_view, name='tickets'),
    path('tickets/<uuid:ticket_id>/', views.staff_ticket_detail_view, name='ticket_detail'),
]
