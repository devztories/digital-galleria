from django.contrib import admin
<<<<<<< HEAD
from django.utils.html import format_html

from .models import (
    PaymentSettings,
    ProductCustomization
)


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):

    list_display = (
        "merchant_name",
        "upi_id",
        "preview_qr",
        "updated_at",
    )

    readonly_fields = (
        "preview_qr",
        "updated_at",
    )

    fieldsets = (

        ("Merchant Information", {

            "fields": (

                "merchant_name",
                "bank_name",
                "upi_id",

            )

        }),

        ("Payment QR", {

            "fields": (

                "qr_code",
                "preview_qr",

            )

        }),

        ("Instructions", {

            "fields": (

                "instructions",

            )

        }),

        ("Information", {

            "fields": (

                "updated_at",

            )

        }),

    )

    def preview_qr(self, obj):

        if obj.qr_code:

            return format_html(

                '<img src="{}" width="180" style="border-radius:10px;" />',

                obj.qr_code.url

            )

        return "No QR Uploaded"

    preview_qr.short_description = "QR Preview"



@admin.register(ProductCustomization)
class ProductCustomizationAdmin(admin.ModelAdmin):

    list_display = (

        "id",

        "customer",

        "product",

        "frame_size",

        "frame_color",

        "photo_preview",

        "created_at",

    )

    list_filter = (

        "frame_size",

        "frame_color",

        "created_at",

    )

    search_fields = (

        "customer__username",

        "product__name",

    )

    readonly_fields = (

        "photo_preview",

        "created_at",

    )

    fieldsets = (

        ("Customer", {

            "fields": (

                "customer",

                "product",

            )

        }),

        ("Customization", {

            "fields": (

                "uploaded_photo",

                "photo_preview",

                "custom_text",

                "font_name",

                "frame_size",

                "frame_color",

                "notes",

            )

        }),

        ("Created", {

            "fields": (

                "created_at",

            )

        }),

    )

    def photo_preview(self, obj):

        if obj.uploaded_photo:

            return format_html(

                '<img src="{}" width="180" style="border-radius:12px;" />',

                obj.uploaded_photo.url

            )

        return "No Image"

    photo_preview.short_description = "Customer Photo"
=======

# Register your models here.
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
