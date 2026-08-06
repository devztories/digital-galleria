from django.urls import path

from . import views


urlpatterns = [

    path(
        "upi/<int:order_id>/",
        views.upi_payment,
        name="upi_payment"
    ),

    path(
        "status/<int:order_id>/",
        views.payment_status,
        name="payment_status"
    ),

]