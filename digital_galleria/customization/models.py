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
    # How the customer dragged/zoomed THIS image inside its chosen shape
    # (see products.PreviewArea, referenced below). offset_x/y are
    # percentages (0-100) of the shape's bounding box; scale is a
    # multiplier (1.0 = fit, no cap in either direction). Blank when this
    # image wasn't placed against any shape.
    preview_offset_x = models.FloatField(null=True, blank=True)
    preview_offset_y = models.FloatField(null=True, blank=True)
    preview_scale = models.FloatField(null=True, blank=True)
    # Which admin-drawn shape (see products.PreviewArea) this particular
    # uploaded image was positioned into. A product can have several shapes
    # on one image (e.g. a 3-photo collage frame) — each uploaded image is
    # placed into its own shape independently. Blank/null when this image
    # wasn't placed against any shape (no preview areas configured, or the
    # customer had more images than available shapes).
    preview_area = models.ForeignKey(
        "products.PreviewArea", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        ordering = ["display_order", "id"]
