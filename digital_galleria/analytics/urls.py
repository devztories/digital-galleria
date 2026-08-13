from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/download-all/', views.download_all_images, name='download_all_images'),
    path('image/<int:image_id>/download/', views.download_image, name='download_image'),
    path('expenses/', views.expense_list, name='expenses'),
]
