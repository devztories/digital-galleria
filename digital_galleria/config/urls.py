from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('creator-studio/', include('creator_studio.urls')),
    path('', include('sitecontent.urls')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('category/', include('categories.urls')),
    path('cart/', include('cart.urls')),
    path('customize/', include('customization.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('coupons/', include('coupons.urls')),
    path('offers/', include('offers.urls')),
    path('ads/', include('advertisements.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('dashboard/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'sitecontent.error_views.error_404'
handler403 = 'sitecontent.error_views.error_403'
handler500 = 'sitecontent.error_views.error_500'
