from django.urls import path
from . import views
app_name='creator_studio'
urlpatterns=[
    path('', views.home, name='home'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
]
