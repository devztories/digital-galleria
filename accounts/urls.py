from django.urls import path
from . import views

<<<<<<< HEAD
=======

>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
urlpatterns = [

    path(
        "register/",
<<<<<<< HEAD
        views.register,
=======
        views.register_view,
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
        name="register"
    ),

    path(
        "login/",
<<<<<<< HEAD
        views.user_login,
=======
        views.login_view,
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
        name="login"
    ),

    path(
        "logout/",
<<<<<<< HEAD
        views.user_logout,
=======
        views.logout_view,
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
        name="logout"
    ),

    path(
        "profile/",
<<<<<<< HEAD
        views.profile,
        name="profile"
    ),

=======
        views.profile_view,
        name="profile"
    ),

    # =========================================================
# SAVED ADDRESSES
# =========================================================

path(
    "addresses/",
    views.saved_addresses,
    name="saved_addresses",
),

path(
    "addresses/add/",
    views.add_address,
    name="add_address",
),

path(
    "addresses/<int:address_id>/edit/",
    views.edit_address,
    name="edit_address",
),

path(
    "addresses/<int:address_id>/default/",
    views.set_default_address,
    name="set_default_address",
),

path(
    "addresses/<int:address_id>/delete/",
    views.delete_address,
    name="delete_address",
),


>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
]