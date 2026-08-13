import os
import uuid
from django.conf import settings
from django.db import models
from products.models import Product


def custom_image_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    safe_name = f'{uuid.uuid4().hex}{ext}'
    return f'customizations/originals/{safe_name}'


class Customization(models.Model):
    """
    Represents a customer's customization choices for a product, prior to
    being attached to a cart item / order item. Preserved permanently once
    attached to an order (see orders.models.OrderItem).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customizations', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='customizations')
    recipient_name = models.CharField(max_length=150, blank=True)
    custom_message = models.TextField(blank=True)
    via_whatsapp = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Customization for {self.product.name} (#{self.pk})'

    @property
    def image_count(self):
        return self.images.count()


class CustomizationImage(models.Model):
    """
    Stores the ORIGINAL uploaded file untouched. This is critical: the file
    saved here must never be re-encoded, resized, or compressed. Any preview
    thumbnail should be generated separately and is not modeled here since
    browsers can downscale via CSS/width attributes for previews without
    touching the underlying file.
    """
    customization = models.ForeignKey(Customization, on_delete=models.CASCADE, related_name='images')
    original_file = models.ImageField(upload_to=custom_image_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text='Size in bytes')
    content_type = models.CharField(max_length=100, blank=True)
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename

    @property
    def file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
