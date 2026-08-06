from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Coupon


# =========================================================
# COUPON ADMIN
# =========================================================

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):


    # =====================================================
    # ADMIN LIST
    # =====================================================

    list_display = (

        "code",

        "discount_percentage",

        "minimum_order_amount",

        "valid_from",

        "valid_until",

        "coupon_status",

        "is_active",

    )


    # =====================================================
    # FILTERS
    # =====================================================

    list_filter = (

        "is_active",

        "valid_from",

        "valid_until",

    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_fields = (

        "code",

    )


    # =====================================================
    # ORDERING
    # =====================================================

    ordering = (

        "-created_at",

    )


    # =====================================================
    # READ ONLY
    # =====================================================

    readonly_fields = (

        "created_at",

        "updated_at",

        "coupon_status_detail",

    )


    # =====================================================
    # FIELD GROUPS
    # =====================================================

    fieldsets = (

        (
            "Coupon Details",

            {

                "fields": (

                    "code",

                    "discount_percentage",

                    "minimum_order_amount",

                )

            },

        ),


        (
            "Coupon Validity",

            {

                "fields": (

                    "valid_from",

                    "valid_until",

                    "is_active",

                    "coupon_status_detail",

                )

            },

        ),


        (
            "System Information",

            {

                "classes": (
                    "collapse",
                ),

                "fields": (

                    "created_at",

                    "updated_at",

                )

            },

        ),

    )


    # =====================================================
    # COUPON STATUS IN LIST
    # =====================================================

    @admin.display(
        description="Status"
    )
    def coupon_status(
        self,
        obj
    ):

        now = timezone.now()


        # MANUALLY DISABLED

        if not obj.is_active:

            return format_html(

                '<strong style="color:#777;">'
                '● Disabled'
                '</strong>'

            )


        # UPCOMING

        if now < obj.valid_from:

            return format_html(

                '<strong style="color:#2563eb;">'
                '● Upcoming'
                '</strong>'

            )


        # EXPIRED

        if now > obj.valid_until:

            return format_html(

                '<strong style="color:#dc2626;">'
                '● Expired'
                '</strong>'

            )


        # ACTIVE

        return format_html(

            '<strong style="color:#16a34a;">'
            '● Active'
            '</strong>'

        )


    # =====================================================
    # DETAILED STATUS
    # =====================================================

    @admin.display(
        description="Current Coupon Status"
    )
    def coupon_status_detail(
        self,
        obj
    ):

        if not obj.pk:

            return (
                "Save the coupon to see "
                "its current status."
            )


        now = timezone.now()


        if not obj.is_active:

            return format_html(

                '<strong style="color:#777;">'
                'This coupon is manually disabled.'
                '</strong>'

            )


        if now < obj.valid_from:

            return format_html(

                '<strong style="color:#2563eb;">'
                'Upcoming coupon — '
                'not available to customers yet.'
                '</strong>'

            )


        if now > obj.valid_until:

            return format_html(

                '<strong style="color:#dc2626;">'
                'This coupon has expired.'
                '</strong>'

            )


        return format_html(

            '<strong style="color:#16a34a;">'
            '✓ This coupon is currently active.'
            '</strong>'

        )