from decimal import Decimal
from django.conf import settings
from django.db import models
from products.models import Product
from customization.models import Customization


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cart #{self.pk}'

    @property
    def items_qs(self):
        return self.items.select_related('product', 'customization')

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items_qs), Decimal('0.00'))

    @property
    def delivery_total(self):
        return sum((item.delivery_total for item in self.items_qs), Decimal('0.00'))

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items_qs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customization = models.ForeignKey(Customization, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def unit_price(self):
        return self.product.price

    @property
    def line_total(self):
        return (self.unit_price or 0) * (self.quantity or 0)

    @property
    def delivery_total(self):
        # Server-side authoritative delivery calculation, see cart.utils
        return (self.product.delivery_charge or 0) * (self.quantity or 0)
