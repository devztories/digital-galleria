from decimal import Decimal
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=12, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    times_used = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid_now(self):
        now = timezone.now()
        if not self.active:
            return False, 'This coupon is no longer active.'
        if now < self.start_date or now > self.expiry_date:
            return False, 'This coupon has expired.'
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, 'This coupon has reached its usage limit.'
        return True, ''

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        """Server-side authoritative discount calculation. Never trust frontend values."""
        if subtotal < self.minimum_order:
            return Decimal('0.00')
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value / Decimal('100'))
        else:
            discount = self.discount_value
        if self.maximum_discount:
            discount = min(discount, self.maximum_discount)
        return min(discount, subtotal)
