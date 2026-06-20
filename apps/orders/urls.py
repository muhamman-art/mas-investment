from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmation/<uuid:pk>/', views.order_confirmation_view, name='order_confirmation'),
    path('history/', views.order_list_view, name='order_list'),
    path('<uuid:pk>/', views.order_detail_view, name='order_detail'),
    path('<uuid:order_id>/receipt/', views.upload_receipt_view, name='upload_receipt'),
]
