from django.db import models
from orders.models import Order

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('verified', 'Verified'),
    ('rejected', 'Rejected'),
)


class PaymentProof(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_proofs')
    screenshot = models.ImageField(upload_to='payment_proofs/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Payment proof for {self.order.order_number}'
