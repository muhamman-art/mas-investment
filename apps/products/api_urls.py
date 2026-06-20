from django.urls import path
from . import api_views

urlpatterns = [
    path('categories/', api_views.CategoryListAPI.as_view(), name='api_categories'),
    path('', api_views.ProductListAPI.as_view(), name='api_products'),
    path('<slug:slug>/', api_views.ProductDetailAPI.as_view(), name='api_product_detail'),
    path('wishlist/', api_views.wishlist_api, name='api_wishlist'),
]
