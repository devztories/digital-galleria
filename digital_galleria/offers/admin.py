from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'discount_text', 'target_gender', 'active', 'start_date', 'end_date', 'display_order')
    list_filter = ('active', 'target_gender')
    list_editable = ('display_order', 'active')
