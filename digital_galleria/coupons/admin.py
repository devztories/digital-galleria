from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'active', 'start_date', 'expiry_date', 'times_used', 'usage_limit')
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)
