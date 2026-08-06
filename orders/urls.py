from django.urls import path
<<<<<<< HEAD
from . import views

urlpatterns = [

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "payment/<int:order_id>/",
        views.payment,
        name="payment"
    ),

    path(
        "success/",
        views.order_success,
        name="order_success"
    ),

    path(
        "history/",
        views.order_history,
        name="orders"
    ),

    path(
        "invoice/<int:order_id>/",
        views.download_invoice,
        name="download_invoice"
    ),
path(
    "detail/<int:order_id>/",
    views.order_detail,
    name="order_detail"
),
=======

from . import views


# =========================================================
# ORDERS URLS
# =========================================================

urlpatterns = [

    # =====================================================
    # CHECKOUT
    # =====================================================

    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),


    # =====================================================
    # APPLY / VALIDATE COUPON
    #
    # Used by checkout page AJAX.
    #
    # Customer clicks:
    #
    # I have a coupon
    #       ↓
    # Enter JUNE20
    #       ↓
    # Apply
    #       ↓
    # AJAX request comes here
    #       ↓
    # Validate coupon + calculate discount
    # =====================================================

    path(
        "apply-coupon/",
        views.apply_coupon,
        name="apply_coupon",
    ),


    # =====================================================
    # MY ORDERS
    # =====================================================

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders",
    ),


    # =====================================================
    # ORDER CONFIRMATION
    # =====================================================

    path(
        "confirmation/<int:order_id>/",
        views.order_confirmation,
        name="order_confirmation",
    ),


    # =====================================================
    # ORDER DETAILS
    # =====================================================

    path(
        "order/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),


    # =====================================================
    # CANCEL ORDER
    # =====================================================

    path(
        "order/<int:order_id>/cancel/",
        views.cancel_order,
        name="cancel_order",
    ),

>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
]