from django.urls import path

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

]