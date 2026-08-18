from django.urls import path
from . import views

app_name = "customization"

urlpatterns = [
    path("<slug:slug>/", views.customize_product, name="customize"),
]
