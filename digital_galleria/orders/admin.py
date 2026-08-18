from django.contrib import admin
from .models import DeliveryCountRule, Order, OrderItem, DeliveryWeightSlab


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name_snapshot", "grand_total", "order_status", "payment_status", "created_date")
    search_fields = ("order_number", "customer_name_snapshot", "phone_snapshot", "email_snapshot")
    inlines = [OrderItemInline]


@admin.register(DeliveryWeightSlab)
class DeliveryWeightSlabAdmin(admin.ModelAdmin):
    list_display = ("min_weight", "max_weight", "charge", "is_active", "priority")
    list_filter = ("is_active",)
    ordering = ("priority", "min_weight")

@admin.register(DeliveryCountRule)
class DeliveryCountRuleAdmin(admin.ModelAdmin):
    list_display = ("min_items", "max_items", "charge", "is_active", "priority")
    list_filter = ("is_active",)
    ordering = ("priority", "min_items")
