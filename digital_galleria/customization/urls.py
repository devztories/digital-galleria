from django.urls import path
from . import views

app_name = 'customization'

urlpatterns = [
    path('start/<int:product_id>/', views.start_customization, name='start'),
]
