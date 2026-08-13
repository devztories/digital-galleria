from django.contrib import admin
from .models import PaymentProof


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'submitted_at', 'verified_at')
    list_filter = ('status',)
    readonly_fields = ('submitted_at',)
