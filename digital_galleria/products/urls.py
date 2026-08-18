from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("search-suggestions/", views.search_suggestions, name="search_suggestions"),
    path("<slug:slug>/", views.product_detail, name="detail"),
]
