from django.contrib import admin
from .models import Advertisement


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_section', 'target_gender', 'active', 'priority', 'full_screen_popup')
    list_filter = ('active', 'target_section', 'target_gender')
    list_editable = ('priority', 'active')
