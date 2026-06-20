"""
MAS Investment - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    # Frontend routes
    path('', include('apps.products.urls', namespace='home')),
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('shop/', include('apps.products.urls_shop', namespace='products')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('customer/', include('apps.accounts.customer_urls', namespace='customer')),
    path('vendor/', include('apps.vendors.urls', namespace='vendor')),
    path('rider/', include('apps.riders.urls', namespace='rider')),
    path('staff/', include('apps.staff.urls', namespace='staff')),
    path('admin-panel/', include('apps.staff.admin_urls', namespace='admin_panel')),
    path('support/', include('apps.support.urls', namespace='support')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    # REST API routes
    path('api/v1/auth/', include('apps.accounts.api_urls')),
    path('api/v1/products/', include('apps.products.api_urls')),
    path('api/v1/orders/', include('apps.orders.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = 'MAS Investment Admin'
admin.site.site_title = 'MAS Investment'
admin.site.index_title = 'Platform Administration'
