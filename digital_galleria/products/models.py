from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from categories.models import Category


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    sku = models.CharField(max_length=64, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    main_image = models.ImageField(upload_to="products/", blank=True, null=True)
    specifications = models.TextField(blank=True, help_text="One 'Key: Value' per line")
    featured = models.BooleanField(default=False)
    bestseller = models.BooleanField(default=False)
    customizable = models.BooleanField(default=False)
    max_customization_images = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Maximum number of reference images a customer can upload "
            "when customizing THIS product. Leave as 0 to use the "
            "site-wide default set in Site Settings."
        ),
    )
    active = models.BooleanField(default=True)

    # Shipment configuration
    weight = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal("0.000"), help_text="Product weight in the selected weight unit.")
    WEIGHT_UNIT_CHOICES = [("kg", "Kilograms"), ("g", "Grams")]
    weight_unit = models.CharField(max_length=2, choices=WEIGHT_UNIT_CHOICES, default="kg")

    # Legacy product-specific delivery settings are retained for compatibility.
    delivery_enabled = models.BooleanField(default=True)
    free_delivery = models.BooleanField(default=False)
    first_item_delivery_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    additional_item_delivery_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.weight is not None and self.weight < 0:
            raise ValidationError({"weight": "Product weight cannot be negative."})
        if self.discount_price is not None and self.discount_price < 0:
            raise ValidationError({"discount_price": "Discount price cannot be negative."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.price:
            return round((1 - (self.discount_price / self.price)) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def spec_list(self):
        items = []
        for line in (self.specifications or "").splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                items.append((k.strip(), v.strip()))
        return items

    def __str__(self):
        return self.name


    @property
    def gallery_images(self):
        return self.images.all()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]
