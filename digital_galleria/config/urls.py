from django.contrib import admin as django_admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from home_views import home_view, policy_view

urlpatterns = [
    path("", home_view, name="home"),
    path("django-admin/", django_admin.site.urls),  # framework fallback, NOT the primary admin UI
    path("admin/", include("dg_admin.urls")),
    path("accounts/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("categories/", include("categories.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("payments/", include("payments.urls")),
    path("customize/", include("customization.urls")),
    path("chat/", include("chatbot.urls")),
    path("policy/<str:page>/", policy_view, name="policy"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")

handler404 = "config.error_views.error_404"
handler500 = "config.error_views.error_500"
handler403 = "config.error_views.error_403"
handler400 = "config.error_views.error_400"
