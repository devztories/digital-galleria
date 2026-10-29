from decimal import Decimal
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPES = [("percentage", "Percentage"), ("flat", "Flat Amount")]

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=12, choices=DISCOUNT_TYPES, default="percentage")
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    per_user_limit = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    # Optional restrictions — leave blank/empty for "applies to everything".
    applicable_products = models.ManyToManyField("products.Product", blank=True, related_name="restricted_coupons")
    applicable_categories = models.ManyToManyField("categories.Category", blank=True, related_name="restricted_coupons")

    def __str__(self):
        return self.code

    def is_currently_valid(self):
        now = timezone.now()
        return self.active and self.start_date <= now <= self.expiry_date

    def validity_error(self):
        """Returns a specific reason the coupon can't be used right now, or None if valid.
        Distinguishes disabled vs not-yet-started vs expired, per the coupon UX spec."""
        if not self.active:
            return "disabled"
        now = timezone.now()
        if now < self.start_date:
            return "not_started"
        if now > self.expiry_date:
            return "expired"
        return None

    def applies_to_lines(self, lines):
        """Checks product/category restrictions against actual checkout lines.
        No restrictions configured => applies to everything."""
        has_product_restriction = self.applicable_products.exists()
        has_category_restriction = self.applicable_categories.exists()
        if not has_product_restriction and not has_category_restriction:
            return True
        for line in lines:
            product = line["product"]
            if has_product_restriction and self.applicable_products.filter(pk=product.pk).exists():
                return True
            if has_category_restriction and product.category_id and self.applicable_categories.filter(pk=product.category_id).exists():
                return True
        return False

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        if subtotal < self.minimum_order:
            return Decimal("0.00")
        if self.discount_type == "percentage":
            discount = subtotal * (self.discount_value / Decimal("100"))
        else:
            discount = self.discount_value
        if self.maximum_discount:
            discount = min(discount, self.maximum_discount)
        return min(discount, subtotal)

    def usage_count(self):
        return self.usages.count()

    def user_usage_count(self, user):
        if not user or not user.is_authenticated:
            return 0
        return self.usages.filter(user=user).count()


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
