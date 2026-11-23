from django.urls import path

from . import views

urlpatterns = [
    path("sw.js", views.service_worker, name="sw"),
    path("poll/", views.poll, name="poll"),
    path("read-all/", views.mark_all_read, name="mark_all_read"),
    path("<int:pk>/read/", views.mark_read, name="mark_read"),
    path("push/subscribe/", views.push_subscribe, name="push_subscribe"),
    path("push/unsubscribe/", views.push_unsubscribe, name="push_unsubscribe"),
    path("push/test/", views.push_test, name="push_test"),
    path("", views.notification_list, name="notifications"),
]
