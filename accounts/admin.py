from django.contrib import admin
from .models import User


class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "phone",
        "city",
        "state"
    )
#=======


