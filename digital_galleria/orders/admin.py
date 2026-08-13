from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.urls import reverse

from .models import Order, OrderItem
from payments.models import PaymentProof


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        'product_name', 'quantity', 'unit_price', 'delivery_charge',
        'customization_snapshot', 'customer_files', 'line_total_display'
    )
    readonly_fields = (
        'product_name', 'quantity', 'unit_price', 'delivery_charge',
        'customization_snapshot', 'customer_files', 'line_total_display'
    )

    @admin.display(description='Customization')
    def customization_snapshot(self, obj):
        if not obj or not obj.customization:
            return format_html('<span style="color:#8f8898">No customization</span>')
        c = obj.customization
        text = f'{c.recipient_name or "—"}'
        if c.custom_message:
            text += f' · {c.custom_message[:90]}'
        return format_html('<div style="max-width:280px"><strong>{}</strong><br><span style="color:#8f8898">{}</span></div>', text, c.product.name)

    @admin.display(description='Customer files')
    def customer_files(self, obj):
        if not obj or not obj.customization:
            return '—'
        images = obj.customization.images.all()
        if not images:
            return format_html('<span style="color:#8f8898">No files</span>')
        links = []
        for image in images:
            if image.original_file:
                links.append(format_html(
                    '<a href="{}" download style="display:inline-block;margin:2px 4px 2px 0;padding:5px 8px;border:1px solid #3b3348;border-radius:8px;color:#cbb7ff;text-decoration:none">↓ {}</a>',
                    image.original_file.url,
                    image.original_filename[:24],
                ))
        return format_html_join('', '{}', ((x,) for x in links))

    @admin.display(description='Line total')
    def line_total_display(self, obj):
        if not obj:
            return '—'
        return f'₹{obj.line_total}'


class PaymentProofInline(admin.TabularInline):
    model = PaymentProof
    extra = 0
    fields = ('proof_preview', 'status', 'admin_note', 'submitted_at', 'verified_at')
    readonly_fields = ('proof_preview', 'submitted_at', 'verified_at')

    @admin.display(description='Payment proof')
    def proof_preview(self, obj):
        if not obj or not obj.screenshot:
            return format_html('<span style="color:#8f8898">No screenshot</span>')
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px">'
            '<a href="{}" target="_blank"><img src="{}" style="width:90px;height:65px;object-fit:cover;border-radius:9px;border:1px solid #3b3348"></a>'
            '<a href="{}" download style="color:#cbb7ff">Download original</a></div>',
            obj.screenshot.url, obj.screenshot.url, obj.screenshot.url
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_badge', 'customer', 'order_status', 'payment_status',
        'customization_status', 'total', 'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'phone', 'user__username')
    date_hierarchy = 'created_at'
    list_per_page = 25
    ordering = ('-created_at',)
    inlines = [OrderItemInline, PaymentProofInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'order_overview')
    fieldsets = (
        ('ORDER COMMAND CENTER', {
            'fields': ('order_overview',),
            'description': 'This single panel contains the customer, payment, customization files, items and delivery status for this order.'
        }),
        ('Customer & Delivery', {
            'fields': ('user', 'full_name', 'email', 'phone', 'address', 'city', 'district', 'state', 'pincode', 'delivery_notes')
        }),
        ('Order & Payment Status', {
            'fields': ('order_number', 'status', 'admin_note', 'subtotal', 'delivery_total', 'discount_total', 'grand_total', 'coupon_code')
        }),
        ('Timeline', {'fields': ('created_at', 'updated_at')}),
    )

    def get_queryset(self, request):
        return (super().get_queryset(request)
                .select_related('user')
                .prefetch_related('items__customization__images', 'payment_proofs'))

    @admin.display(description='Order', ordering='order_number')
    def order_badge(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.pk])
        return format_html('<a href="{}" style="font-weight:850;color:#cbb7ff">#{}</a>', url, obj.order_number)

    @admin.display(description='Customer')
    def customer(self, obj):
        return format_html('<strong>{}</strong><br><span style="color:#8f8898">{} · {}</span>', obj.full_name, obj.email, obj.phone)

    @admin.display(description='Status', ordering='status')
    def order_status(self, obj):
        cls = 'ok' if obj.status in ('payment_verified','processing','ready','shipped','delivered') else 'warn'
        return format_html('<span class="dg-status {}">{}</span>', cls, obj.get_status_display())

    @admin.display(description='Payment')
    def payment_status(self, obj):
        proofs = list(obj.payment_proofs.all())
        if not proofs:
            return format_html('<span class="dg-status warn">No proof</span>')
        latest = proofs[0]
        return format_html('<span class="dg-status {}">{} · {} proof{}</span>',
                           'ok' if latest.status == 'verified' else 'warn',
                           latest.get_status_display(), len(proofs), '' if len(proofs) == 1 else 's')

    @admin.display(description='Customization')
    def customization_status(self, obj):
        items = list(obj.items.all())
        custom_items = [i for i in items if i.customization_id]
        files = sum(i.customization.image_count for i in custom_items if i.customization)
        if not custom_items:
            return format_html('<span class="dg-status neutral">None</span>')
        return format_html('<span class="dg-status ok">{} item · {} file{}</span>', len(custom_items), files, '' if files == 1 else 's')

    @admin.display(description='Total', ordering='grand_total')
    def total(self, obj):
        return format_html('<strong>₹{}</strong>', obj.grand_total)

    @admin.display(description='Complete order summary')
    def order_overview(self, obj):
        items = list(obj.items.all())
        proofs = list(obj.payment_proofs.all())
        customizations = [i.customization for i in items if i.customization]
        file_count = sum(c.image_count for c in customizations)
        verified = sum(1 for p in proofs if p.status == 'verified')
        return format_html(
            '<div class="dg-order-overview">'
            '<div class="dg-overview-grid">'
            '<div><small>ORDER</small><strong>#{}</strong></div>'
            '<div><small>STATUS</small><strong>{}</strong></div>'
            '<div><small>PAYMENT</small><strong>{}/{} verified</strong></div>'
            '<div><small>CUSTOMIZATION</small><strong>{} item · {} file{}</strong></div>'
            '<div><small>TOTAL</small><strong>₹{}</strong></div>'
            '<div><small>CREATED</small><strong>{}</strong></div>'
            '</div>'
            '<div class="dg-overview-note">Everything belonging to this order is below: line items, original customer files, payment proofs, status and admin notes. No need to jump between separate admin sections.</div>'
            '</div>',
            obj.order_number, obj.get_status_display(), verified, len(proofs), len(customizations), file_count,
            '' if file_count == 1 else 's', obj.grand_total, obj.created_at.strftime('%d %b %Y, %I:%M %p')
        )

    class Media:
        css = {'all': ('admin/dg_order.css',)}
