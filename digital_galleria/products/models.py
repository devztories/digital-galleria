from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from categories.models import Category


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    keywords = models.CharField(max_length=255, blank=True, help_text='Comma separated search keywords')

    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percent = models.PositiveIntegerField(default=0)

    main_image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)

    customizable = models.BooleanField(default=False)
    max_custom_images = models.PositiveIntegerField(default=1)

    # Per-product delivery charge (MANDATORY business rule):
    # The delivery charge stored here is ALWAYS the authoritative value.
    # It is never trusted from the frontend; server always re-reads this field
    # at cart/checkout time. See cart.utils.calculate_delivery for the rule.
    delivery_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])

    @property
    def stock_status(self):
        if self.stock <= 0:
            return 'out'
        if self.stock <= 5:
            return 'low'
        return 'in'

    @property
    def in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f'{self.product.name} image #{self.pk}'
