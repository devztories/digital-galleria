from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_view, name="checkout"),
    path("checkout/step-1/", views.checkout_step1, name="checkout_step1"),
    path("checkout/step-2/", views.checkout_step2, name="checkout_step2"),
    path("checkout/apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("checkout/delivery-state/", views.checkout_delivery_state, name="checkout_delivery_state"),
    path("checkout/place/", views.place_order, name="place_order"),
    path("<str:order_number>/details/", views.order_detail_view, name="order_detail"),
    path("<str:order_number>/cancel/", views.cancel_order, name="cancel_order"),
    path("<str:order_number>/", views.tracking_view, name="tracking"),
]
