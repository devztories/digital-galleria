from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("<str:order_number>/pay/", views.pay_view, name="pay"),
    path("<str:order_number>/status/", views.success_view, name="success"),
    path("<str:order_number>/qr-download/", views.qr_download, name="qr_download"),
]
