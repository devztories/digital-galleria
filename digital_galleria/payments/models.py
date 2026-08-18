from django.db import models


class Payment(models.Model):
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="payment")
    transaction_reference = models.CharField(max_length=100, blank=True)
    proof_image = models.ImageField(upload_to="payments/proofs/", blank=True, null=True)
    rejection_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.order.order_number}"
