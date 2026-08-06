from django.urls import path
<<<<<<< HEAD
from . import views

urlpatterns = [
    path("", views.cart, name="cart"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update/<int:product_id>/", views.update_cart, name="update_cart"),
=======

from . import views


urlpatterns = [

    # =====================================================
    # CART
    # =====================================================

    path(
        "",
        views.cart_detail,
        name="cart_detail",
    ),


    # =====================================================
    # ADD NORMAL PRODUCT
    # =====================================================

    path(
        "add/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart",
    ),


    # =====================================================
    # ADD CUSTOMIZED PRODUCT
    # =====================================================

    path(
        "add-customized/<int:product_id>/<int:customization_id>/",
        views.add_customized_to_cart,
        name="add_customized_to_cart",
    ),


    # =====================================================
    # INCREASE
    #
    # <str:cart_key> is important because customized
    # keys look like:
    #
    # custom_5
    # =====================================================

    path(
        "increase/<str:cart_key>/",
        views.increase_quantity,
        name="increase_quantity",
    ),


    # =====================================================
    # DECREASE
    # =====================================================

    path(
        "decrease/<str:cart_key>/",
        views.decrease_quantity,
        name="decrease_quantity",
    ),


    # =====================================================
    # REMOVE
    # =====================================================

    path(
        "remove/<str:cart_key>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),

>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
]