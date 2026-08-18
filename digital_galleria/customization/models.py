from django.db import models


class Customization(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="customizations")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="customizations")
    details = models.TextField(blank=True, help_text="Optional customer-entered customization details")
    reference_image = models.ImageField(upload_to="customization/reference/", blank=True, null=True)
    customized_image = models.ImageField(upload_to="customization/output/", blank=True, null=True)
    via_whatsapp = models.BooleanField(default=False)
    whatsapp_message = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customization #{self.pk} - {self.product.name}"


class CustomizationImage(models.Model):
    customization = models.ForeignKey(Customization, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="customization/reference/")
    display_order = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "id"]
