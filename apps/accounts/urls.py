"""accounts/urls.py"""
from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<uuid:token>/', views.verify_email_view, name='verify_email'),
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/<uuid:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('profile/', views.profile_view, name='profile'),
]
