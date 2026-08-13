from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.GalleriaLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/profile/', views.profile_view, name='profile'),
    path('settings/theme/', views.theme_view, name='theme'),
    path('settings/orders/', views.my_orders_view, name='my_orders'),
]
