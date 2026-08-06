<<<<<<< HEAD
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
=======
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum

from .models import (
    Order,
    OrderItem,
    ProductCustomization,
    ProductCustomizationImage,
)

from products.models import Product
class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    can_delete = False

    show_change_link = True

>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
    readonly_fields = (
        "product",
        "quantity",
        "price",
<<<<<<< HEAD
    )


=======
        "item_subtotal",
        "customization_preview",
    )

    fields = (
        "product",
        "quantity",
        "price",
        "item_subtotal",
        "customization_preview",
    )

    @admin.display(description="Subtotal")
    def item_subtotal(self, obj):
        return f"₹{obj.price * obj.quantity:.2f}"

    @admin.display(description="Customization")
    def customization_preview(self, obj):

        if not obj.customization:
            return "-"

        if getattr(obj.customization, "preview_image", None):

            try:
                return format_html(
                    '<img src="{}" style="height:80px;border-radius:6px;">',
                    obj.customization.preview_image.url
                )

            except Exception:
                pass

        return "No Preview"
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
<<<<<<< HEAD
        "user",
        "full_name",
        "total_price",
        "payment_method",
        "payment_status",
        "status",
=======
        "name",
        "user",
        "payment_status",
        "status",
        "total_amount",
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
        "created_at",
    )

    list_filter = (
<<<<<<< HEAD
        "payment_status",
        "payment_method",
        "status",
    )

    search_fields = (
        "user__username",
        "full_name",
        "transaction_id",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (

        ("Customer Details", {
            "fields": (
                "user",
                "full_name",
                "phone",
                "address",
                "city",
                "state",
                "pincode",
            )
        }),

        ("Order Details", {
            "fields": (
                "total_price",
                "status",
            )
        }),

        ("Payment Details", {
            "fields": (
                "payment_method",
                "payment_status",
                "transaction_id",
                "payment_screenshot",
            )
        }),

        ("Other", {
            "fields": (
                "created_at",
=======
        "status",
        "payment_status",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "id",
        "name",
        "email",
        "phone",
        "tracking_id",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    list_per_page = 25

    inlines = [OrderItemInline]
    readonly_fields = (
        "created_at",
        "updated_at",
        "subtotal",
        "discount_amount",
        "total_amount",
    )
    fieldsets = (

        ("Customer Information", {
            "fields": (
                "user",
                "name",
                "email",
                "phone",
            )
        }),

        ("Shipping Address", {
            "fields": (
                "address",
                "city",
                "state",
                "postal_code",
            )
        }),

        ("Payment Information", {
            "fields": (
                "payment_method",
                "payment_status",
            )
        }),

        ("Order Status", {
            "fields": (
                "status",
                "tracking_id",
                "courier_name",
                "expected_delivery_date",
            )
        }),

        ("Price Details", {
            "fields": (
                "subtotal",
                "coupon_code",
                "coupon_discount_percentage",
                "discount_amount",
                "total_amount",
            )
        }),

        ("Refund / Cancellation", {
            "fields": (
                "cancellation_status",
                "cancellation_reason",
                "refund_status",
                "refund_reference",
            )
        }),

        ("Dates", {
            "fields": (
                "created_at",
                "updated_at",
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
            )
        }),

    )
<<<<<<< HEAD

    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "product",
        "quantity",
        "price",
    )
=======
    @admin.display(description="Total Amount")
    def formatted_total(self, obj):
        return f"₹{obj.total_amount:.2f}"


    @admin.action(description="Mark selected orders as Processing")
    def mark_processing(self, request, queryset):

        updated = queryset.update(status="Processing")

        self.message_user(
            request,
            f"{updated} order(s) updated.",
            messages.SUCCESS,
        )


    @admin.action(description="Mark selected orders as Shipped")
    def mark_shipped(self, request, queryset):

        updated = queryset.update(status="Shipped")

        self.message_user(
            request,
            f"{updated} order(s) updated.",
            messages.SUCCESS,
        )


    @admin.action(description="Mark selected orders as Delivered")
    def mark_delivered(self, request, queryset):

        updated = queryset.update(status="Delivered")

        self.message_user(
            request,
            f"{updated} order(s) updated.",
            messages.SUCCESS,
        )


    actions = (
        "mark_processing",
        "mark_shipped",
        "mark_delivered",
    )
@admin.register(ProductCustomization)
class ProductCustomizationAdmin(admin.ModelAdmin):

    list_display = (
    "id",
    "user",
    "product",
    "submission_method",
    "is_finalized",
    "created_at",
    "preview_image_display",
)
    list_filter = (
        "is_finalized",
        "created_at",
        "product",
    )

    search_fields = (
        "id",
        "user__username",
        "user__email",
        "product__name",
        "name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
    "created_at",
    "preview_image_display",
    "original_image_display",
)

    list_per_page = 25
    fieldsets = (

        ("Basic Information", {
            "fields": (
                "user",
                "product",
                "name",
                "quantity",
                "is_finalized",
            )
        }),

        ("Images", {
            "fields": (
                "original_image",
                "preview_image",
                "original_image_display",
                "preview_image_display",
            )
        }),

        ("Position", {
            "fields": (
                "position_x",
                "position_y",
                "scale",
                "rotation",
            )
        }),

        ("Instructions", {
            "fields": (
                "instructions",
            )
        }),

        ("Dates", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),

    )
    @admin.display(description="Preview")
    def preview_image_display(self, obj):

        if not obj.preview_image:
            return "-"

        try:
            return format_html(
                '<img src="{}" style="height:120px;border-radius:8px;border:1px solid #ddd;">',
                obj.preview_image.url,
            )
        except Exception:
            return "-"
    @admin.display(description="Original")
    def original_image_display(self, obj):

        if not obj.original_image:
            return "-"

        try:
            return format_html(
                '<img src="{}" style="height:120px;border-radius:8px;border:1px solid #ddd;">',
                obj.original_image.url,
            )
        except Exception:
            return "-"
class ProductCustomizationImageInline(admin.TabularInline):

    model = ProductCustomizationImage

    extra = 0

    readonly_fields = (
        "image_preview",
        "created_at",
    )

    fields = (
        "image",
        "position",
        "image_preview",
        "created_at",
    )

    @admin.display(description="Preview")
    def image_preview(self, obj):

        if not obj.image:
            return "-"

        try:
            return format_html(
                '<img src="{}" style="height:100px;border-radius:8px;">',
                obj.image.url,
            )
        except Exception:
            return "-"
@admin.register(ProductCustomizationImage)
class ProductCustomizationImageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customization",
        "position",
        "created_at",
        "preview",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "customization__id",
    )

    readonly_fields = (
        "preview",
        "created_at",
    )

    @admin.display(description="Image")
    def preview(self, obj):

        if not obj.image:
            return "-"

        try:
            return format_html(
                '<img src="{}" style="height:120px;border-radius:8px;">',
                obj.image.url,
            )
        except Exception:
            return "-"
def mark_as_completed(modeladmin, request, queryset):

    queryset.update(status="Delivered")


mark_as_completed.short_description = "Mark selected orders as Delivered"
admin.site.site_header = "Digital Galleria Admin"

admin.site.site_title = "Digital Galleria"

admin.site.index_title = "Administration Panel"
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
