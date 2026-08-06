from django.urls import path

from . import views

urlpatterns = [

    path(

        "product/<int:product_id>/",

        views.customize_product,

        name="customize_product",

    ),

]