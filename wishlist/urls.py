from django.urls import path
from . import views

urlpatterns=[

path("",views.wishlist,name="wishlist"),

path("add/<int:product_id>/",views.add_wishlist,name="add_wishlist"),

path("remove/<int:product_id>/",views.remove_wishlist,name="remove_wishlist"),

]