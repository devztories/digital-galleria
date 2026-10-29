from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("menu/", views.account_hub_view, name="hub"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("orders/", views.my_orders_view, name="my_orders"),
    path("addresses/", views.addresses_view, name="addresses"),
    path("addresses/<int:pk>/delete/", views.delete_address_view, name="delete_address"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/account/", views.settings_account_view, name="settings_account"),
    path("settings/orders/", views.settings_orders_view, name="settings_orders"),
    path("settings/theme/", views.settings_theme_view, name="settings_theme"),
    path("settings/vehicle/", views.settings_vehicle_view, name="settings_vehicle"),
    path("settings/customization/", views.settings_customization_view, name="settings_customization"),
    path("settings/password/", views.change_password_view, name="change_password"),
]
