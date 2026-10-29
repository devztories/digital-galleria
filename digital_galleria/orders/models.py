from decimal import Decimal
from django.db import models, transaction


def generate_order_number():
    """
    Sequential order numbers: DG{n}. The starting/next value is admin-settable
    (Site Settings → Business → "Next order number") — once set, every
    subsequent order just counts up automatically (DG3002, DG3003, DG3004...).
    Uses select_for_update so concurrent checkouts can never be handed the
    same number.
    """
    from site_settings.models import SiteSettings
    with transaction.atomic():
        settings_obj = SiteSettings.objects.select_for_update().filter(pk=1).first()
        if settings_obj is None:
            settings_obj = SiteSettings.load()
        while True:
            seq = settings_obj.next_order_sequence
            settings_obj.next_order_sequence = seq + 1
            settings_obj.save(update_fields=["next_order_sequence"])
            number = f"DG{seq}"
            # Defensive: skip past any number that's already in use (e.g. from
            # manually-entered historical data) rather than risk a collision.
            if not Order.objects.filter(order_number=number).exists():
                return number


class Order(models.Model):
    # "awaiting_payment" is a pre-confirmation state: the order row already
    # exists (so we have an order_number + reserved stock) but the customer
    # has not yet supplied a payment screenshot or UTR number. Nothing that
    # counts as a "placed order" anywhere in the app (customer order list,
    # tracking page, admin dashboards/stats, cart clearing) should treat an
    # order in this state as real until it moves to "verified".
    STATUS_CHOICES = [
        ("awaiting_payment", "Awaiting Payment"),
        ("verified", "Verified"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    # Statuses admin should be able to manually set an order to. Deliberately
    # excludes "awaiting_payment" — that state is system-managed only and is
    # entered exactly once, automatically, when the order row is first created.
    ADMIN_STATUS_CHOICES = [c for c in STATUS_CHOICES if c[0] != "awaiting_payment"]
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("received", "Payment Received"),
        ("rejected", "Payment Rejected"),
    ]

    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="orders")

    # Idempotency key generated once when the customer reaches the final
    # confirmation step. place_order() re-uses it as a lookup key so that a
    # refresh / back-forward / double-click / payment-page reload can never
    # create a second Order for the same checkout attempt.
    checkout_token = models.CharField(max_length=40, unique=True, null=True, blank=True, editable=False)

    # Snapshots — never change once order is placed
    customer_name_snapshot = models.CharField(max_length=150)
    phone_snapshot = models.CharField(max_length=20)
    email_snapshot = models.EmailField()
    delivery_address_snapshot = models.TextField()

    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_weight = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("0.000"), help_text="Shipment weight snapshot in kg.")
    delivery_method_snapshot = models.CharField(
        max_length=13,
        choices=[("weight", "Weight Based"), ("count", "Product Count Based"), ("product_state", "Per-Product (Kerala / Outside Kerala)")],
        blank=True, help_text="Delivery calculation method active when this order was placed.",
    )
    delivery_quantity_snapshot = models.PositiveIntegerField(default=0, help_text="Total product quantity in the cart when this order was placed (count mode).")
    delivery_rule_label_snapshot = models.CharField(max_length=120, blank=True, help_text="Human-readable description of the delivery rule/slab that was applied.")
    delivery_state_snapshot = models.CharField(max_length=100, blank=True, help_text="Delivery address state used for Kerala/outside-Kerala delivery pricing.")
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.SET_NULL, null=True, blank=True)

    payment_method = models.CharField(max_length=30, default="UPI/QR")
    payment_status = models.CharField(max_length=12, choices=PAYMENT_STATUS_CHOICES, default="pending")
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="awaiting_payment")

    # Remembers whether this order came from Direct Checkout (Buy Now) rather
    # than the cart, so that once payment proof is confirmed we know whether
    # to clear the cart or just drop the buy-now session — without relying on
    # session state that may have changed by the time payment is confirmed.
    is_buy_now = models.BooleanField(default=False)

    expected_delivery_date = models.DateField(blank=True, null=True)
    delivered_date = models.DateField(blank=True, null=True, help_text="Stamped automatically the moment the order status first becomes 'Delivered'.")
    refund_status = models.CharField(max_length=12, choices=[("none", "None"), ("pending", "Pending"), ("completed", "Completed")], default="none")
    cancellation_reason = models.TextField(blank=True)
    stock_deducted = models.BooleanField(
        default=False,
        help_text="Whether product/variant stock has been decremented for this order yet. "
                   "Stock is only deducted once the order reaches 'Processing' (or later) — "
                   "not at order placement/payment time — and is restored automatically if a "
                   "processed order is later cancelled.",
    )

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        previous = None
        if self.pk:
            previous = Order.objects.filter(pk=self.pk).values("order_status", "payment_status", "stock_deducted").first()
        if previous:
            # Admin moving an order out of "verified" into processing/shipped/
            # delivered is treated as confirmation the payment came through —
            # auto-verify it instead of leaving it stuck on "pending".
            if (previous["order_status"] == "verified" and self.order_status in ("processing", "shipped", "delivered")
                    and self.payment_status == "pending"):
                self.payment_status = "received"
            # Stamp delivered_date exactly once, the moment the order first
            # reaches "delivered" — never overwritten on later saves.
            if previous["order_status"] != "delivered" and self.order_status == "delivered" and not self.delivered_date:
                from django.utils import timezone
                self.delivered_date = timezone.now().date()
        super().save(*args, **kwargs)
        if previous:
            # Stock is only ever touched here — never at order placement or
            # payment confirmation. It's deducted the moment an order first
            # reaches "Processing" (or is moved straight to a later stage),
            # and restored automatically if a since-processed order is later
            # cancelled. Centralized here so every path that changes
            # order_status (admin edit, customer cancellation, any future
            # bulk action that goes through .save()) behaves consistently.
            stages = ["awaiting_payment", "verified", "processing", "shipped", "delivered"]

            def stage_index(status):
                return stages.index(status) if status in stages else -1

            was_processed_or_later = stage_index(previous["order_status"]) >= stage_index("processing")
            is_processed_or_later = stage_index(self.order_status) >= stage_index("processing")
            if not previous["stock_deducted"] and not was_processed_or_later and is_processed_or_later:
                from .services.stock import deduct_stock_for_order
                deduct_stock_for_order(self)
            elif previous["stock_deducted"] and self.order_status == "cancelled" and previous["order_status"] != "cancelled":
                from .services.stock import restock_order
                restock_order(self)

    def status_progress(self):
        """Returns list of (stage, is_reached) for the tracking timeline."""
        stages = ["verified", "processing", "shipped", "delivered"]
        if self.order_status in ("cancelled", "awaiting_payment"):
            return []
        current_index = stages.index(self.order_status) if self.order_status in stages else 0
        return [(s, i <= current_index) for i, s in enumerate(stages)]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.SET_NULL, null=True)
    product_name_snapshot = models.CharField(max_length=200)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    customization = models.ForeignKey(
        "customization.Customization", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Colour variant — kept as a live FK (for admin cross-reference) PLUS a
    # full historical snapshot, so this OrderItem never changes even if the
    # admin later edits/deletes the product, variant, colour, or SKU.
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    colour_name_snapshot = models.CharField(max_length=60, blank=True)
    colour_hex_snapshot = models.CharField(max_length=7, blank=True)
    sku_snapshot = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        if self.colour_name_snapshot:
            return f"{self.product_name_snapshot} ({self.colour_name_snapshot}) x{self.quantity}"
        return f"{self.product_name_snapshot} x{self.quantity}"


class DeliveryWeightSlab(models.Model):
    """Administrator-controlled weight slab for shipment delivery pricing."""
    min_weight = models.DecimalField(max_digits=8, decimal_places=3)
    max_weight = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text="Leave blank for an open-ended slab.")
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0, help_text="Lower numbers are evaluated first.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "min_weight", "id"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_weight < 0:
            raise ValidationError({"min_weight": "Minimum weight cannot be negative."})
        if self.max_weight is not None and self.max_weight <= self.min_weight:
            raise ValidationError({"max_weight": "Maximum weight must be greater than minimum weight."})
        if self.charge < 0:
            raise ValidationError({"charge": "Delivery charge cannot be negative."})
        if not self.is_active:
            return
        qs = DeliveryWeightSlab.objects.filter(is_active=True).exclude(pk=self.pk)
        for other in qs:
            other_max = other.max_weight
            this_max = self.max_weight
            overlaps = (this_max is None or other.min_weight < this_max) and (other_max is None or self.min_weight < other_max)
            if overlaps:
                raise ValidationError("Active delivery weight slabs cannot overlap.")

    def __str__(self):
        end = f"{self.max_weight} kg" if self.max_weight is not None else "∞ kg"
        return f"{self.min_weight}–{end} · ₹{self.charge}"


class DeliveryCountRule(models.Model):
    min_items = models.PositiveIntegerField()
    max_items = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for an open-ended rule.")
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["priority", "min_items", "id"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_items < 1:
            raise ValidationError({"min_items": "Minimum item count must be at least 1."})
        if self.max_items is not None and self.max_items < self.min_items:
            raise ValidationError({"max_items": "Maximum item count must be greater than or equal to minimum item count."})
        if self.charge < 0:
            raise ValidationError({"charge": "Delivery charge cannot be negative."})
        if self.is_active:
            qs = DeliveryCountRule.objects.filter(is_active=True).exclude(pk=self.pk)
            for other in qs:
                overlaps = (self.max_items is None or other.min_items <= self.max_items) and (other.max_items is None or self.min_items <= other.max_items)
                if overlaps:
                    raise ValidationError("Active product-count delivery rules cannot overlap.")

    def __str__(self):
        end = self.max_items if self.max_items is not None else "∞"
        return f"{self.min_items}–{end} items · ₹{self.charge}"
