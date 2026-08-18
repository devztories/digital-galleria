import random
import string
from decimal import Decimal
from django.db import models


def generate_order_number():
    while True:
        number = "DG" + "".join(random.choices(string.digits, k=6))
        if not Order.objects.filter(order_number=number).exists():
            return number


class Order(models.Model):
    STATUS_CHOICES = [
        ("verified", "Verified"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("received", "Payment Received"),
        ("rejected", "Payment Rejected"),
    ]

    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="orders")

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
    delivery_method_snapshot = models.CharField(max_length=10, choices=[("weight", "Weight Based"), ("count", "Product Count Based")], blank=True, help_text="Delivery calculation method active when this order was placed.")
    delivery_quantity_snapshot = models.PositiveIntegerField(default=0, help_text="Total product quantity in the cart when this order was placed (count mode).")
    delivery_rule_label_snapshot = models.CharField(max_length=120, blank=True, help_text="Human-readable description of the delivery rule/slab that was applied.")
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.SET_NULL, null=True, blank=True)

    payment_method = models.CharField(max_length=30, default="UPI/QR")
    payment_status = models.CharField(max_length=12, choices=PAYMENT_STATUS_CHOICES, default="pending")
    order_status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="verified")

    expected_delivery_date = models.DateField(blank=True, null=True)
    refund_status = models.CharField(max_length=12, choices=[("none", "None"), ("pending", "Pending"), ("completed", "Completed")], default="none")
    cancellation_reason = models.TextField(blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return self.order_number

    def status_progress(self):
        """Returns list of (stage, is_reached) for the tracking timeline."""
        stages = ["verified", "processing", "shipped", "delivered"]
        if self.order_status == "cancelled":
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

    def __str__(self):
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
