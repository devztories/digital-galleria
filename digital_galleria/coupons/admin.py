from django.contrib import admin
from .models import Coupon, CouponUsage

admin.site.register(Coupon)
admin.site.register(CouponUsage)
