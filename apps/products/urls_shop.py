from django.urls import path
from . import views

app_name = 'products'
urlpatterns = [
    path('', views.shop_view, name='shop'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<uuid:item_id>/', views.update_cart_view, name='update_cart'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<uuid:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
]
