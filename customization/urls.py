from django.urls import path
from . import views

app_name = "customization"

urlpatterns = [
    path("cart-item/<str:cart_key>/", views.customize_cart_item, name="customize_cart_item"),
    path("image/<int:image_id>/remove/", views.remove_customization_image, name="remove_customization_image"),
    path("image/<int:image_id>/download/", views.download_customization_image, name="download_customization_image"),
    path("<slug:slug>/", views.customize_product, name="customize"),
]
