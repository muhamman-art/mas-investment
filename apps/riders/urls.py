from django.urls import path
from . import views

app_name = 'rider'
urlpatterns = [
    path('', views.rider_dashboard_view, name='dashboard'),
    path('deliveries/', views.rider_deliveries_view, name='deliveries'),
    path('deliveries/<uuid:assignment_id>/', views.rider_delivery_detail_view, name='delivery_detail'),
    path('deliveries/<uuid:assignment_id>/update/', views.update_delivery_status_view, name='update_status'),
    path('availability/', views.toggle_availability_view, name='toggle_availability'),
]
