from django.contrib import admin
from .models import Payment, PaymentSettings


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "amount",
        "status",
        "upi_transaction_id",
        "submitted_at",
        "verified_at",
    )

    list_filter = (
        "status",
        "submitted_at",
        "verified_at",
    )

    search_fields = (
        "order__order_id",
        "upi_transaction_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    actions = (
        "mark_paid",
        "mark_rejected",
    )

    def mark_paid(self, request, queryset):
        queryset.update(status="Paid")

    mark_paid.short_description = "Mark selected payments as Paid"

    def mark_rejected(self, request, queryset):
        queryset.update(status="Rejected")

    mark_rejected.short_description = "Mark selected payments as Rejected"


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "upi_receiver_name",
        "upi_id",
        "updated_at",
    )