from django.contrib import admin
<<<<<<< HEAD
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "phone",
        "city",
        "state"
    )
=======

# Register your models here.
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
