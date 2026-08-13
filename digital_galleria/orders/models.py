from decimal import Decimal
from django.conf import settings
from django.db import models
from products.models import Product
from customization.models import Customization


STATUS_CHOICES = (
    ('pending_payment', 'Pending Payment'),
    ('payment_submitted', 'Payment Submitted'),
    ('payment_verified', 'Payment Verified'),
    ('processing', 'Processing'),
    ('ready', 'Ready'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
)

TRACKING_STEPS = ['payment_verified', 'processing', 'shipped', 'delivered']


class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Customer / shipping details (snapshot at time of order)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    delivery_notes = models.TextField(blank=True)

    # Gender snapshot, used ONLY for tracking-animation selection so that a
    # later change to the user's profile never alters a past order's UI.
    gender_snapshot = models.CharField(max_length=10, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    coupon_code = models.CharField(max_length=32, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils.crypto import get_random_string
            self.order_number = 'DG' + get_random_string(6, allowed_chars='0123456789')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order #{self.order_number}'

    @property
    def tracking_gender(self):
        """Used ONLY for tracking animation. Never sourced from theme."""
        return self.gender_snapshot or 'male'

    @property
    def current_step_index(self):
        if self.status in TRACKING_STEPS:
            return TRACKING_STEPS.index(self.status)
        if self.status in ('pending_payment', 'payment_submitted'):
            return -1
        return len(TRACKING_STEPS) - 1


class OrderItem(models.Model):
    """
    Snapshot of a purchased line item. Product/price/delivery/customization
    are copied at order-creation time so future product edits never alter
    historical orders.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    customization = models.ForeignKey(Customization, on_delete=models.SET_NULL, null=True, blank=True)

    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    recipient_name = models.CharField(max_length=150, blank=True)
    custom_message = models.TextField(blank=True)
    via_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def line_total(self):
        return (self.unit_price or 0) * (self.quantity or 0)

    @property
    def line_delivery(self):
        return self.delivery_charge * self.quantity
