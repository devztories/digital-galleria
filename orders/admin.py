from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import DeliveryCountRule, Order, OrderItem, DeliveryWeightSlab


class OrderItemInline(admin.TabularInline):
    """Shows PRODUCT + COLOUR + VARIANT + SKU + QUANTITY + customization
    together for every item, as required by the admin order spec — never
    just the product name alone."""
    model = OrderItem
    extra = 0
    fields = ("product_colour_display", "sku_snapshot", "quantity", "price_snapshot", "subtotal", "customization_preview")
    readonly_fields = ("product_colour_display", "sku_snapshot", "customization_preview")

    def product_colour_display(self, obj):
        if not obj or not obj.pk:
            return "—"
        if obj.colour_name_snapshot:
            return format_html(
                '<strong>{}</strong><br>'
                '<span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
                'background:{};border:1px solid #ccc;vertical-align:middle;"></span> '
                'Colour: {}',
                obj.product_name_snapshot, obj.colour_hex_snapshot or "#ccc", obj.colour_name_snapshot,
            )
        return format_html("<strong>{}</strong>", obj.product_name_snapshot)
    product_colour_display.short_description = "Product / Colour"

    def customization_preview(self, obj):
        if not obj or not obj.customization_id:
            return "—"
        c = obj.customization
        thumbs = []
        for img in c.images.all()[:4]:
            # Original, full-resolution file — never a compressed thumbnail —
            # opens for inline preview; the Download link streams that same
            # original through a server-side view with a forced
            # Content-Disposition, so it downloads correctly regardless of
            # the storage backend's own CDN headers (Supabase Storage in prod).
            download_url = reverse("customization:download_customization_image", args=[img.id])
            thumbs.append(format_html(
                '<span style="display:inline-block;margin:0 6px 6px 0;text-align:center;">'
                '<a href="{}" target="_blank" title="Full-size preview"><img src="{}" '
                'style="height:44px;border-radius:4px;display:block;"></a>'
                '<a href="{}" title="Download original, full quality" style="font-size:10px;">⬇ Original</a>'
                '</span>',
                img.image.url, img.image.url, download_url,
            ))
        if not thumbs and c.reference_image:
            thumbs.append(format_html(
                '<span style="display:inline-block;text-align:center;">'
                '<a href="{}" target="_blank" title="Full-size preview"><img src="{}" '
                'style="height:44px;border-radius:4px;display:block;"></a>'
                '</span>', c.reference_image.url, c.reference_image.url,
            ))
        return format_html("".join(str(t) for t in thumbs)) if thumbs else "No images"
    customization_preview.short_description = "Customization"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name_snapshot", "item_summary", "grand_total", "order_status", "payment_status", "created_date")
    search_fields = ("order_number", "customer_name_snapshot", "phone_snapshot", "email_snapshot")
    readonly_fields = ("delivered_date",)
    inlines = [OrderItemInline]

    def item_summary(self, obj):
        parts = []
        for item in obj.items.all()[:3]:
            label = f"{item.product_name_snapshot}"
            if item.colour_name_snapshot:
                label += f" ({item.colour_name_snapshot})"
            parts.append(f"{label} x{item.quantity}")
        text = ", ".join(parts)
        if obj.items.count() > 3:
            text += f" +{obj.items.count() - 3} more"
        return text
    item_summary.short_description = "Items"


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
