from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<str:order_number>/', views.payment_page, name='payment'),
    path('track/<str:order_number>/', views.track_order, name='track'),
]
