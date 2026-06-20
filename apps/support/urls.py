from django.urls import path
from . import views

app_name = 'support'
urlpatterns = [
    path('', views.customer_tickets_view, name='tickets'),
    path('new/', views.create_ticket_view, name='create_ticket'),
    path('<uuid:ticket_id>/', views.customer_ticket_detail_view, name='ticket_detail'),
]
