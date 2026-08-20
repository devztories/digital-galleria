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
    def storefront_in_stock(self):
        """The stock status that should actually be shown to shoppers.
        For products with colour variants, availability comes from the
        variants (any active colour with stock > 0), not the base Product.stock
        field — admins manage stock per-colour once variants exist, so the
        base field is often left at 0 and should not be treated as truth."""
        if self.has_colour_variants:
            return self.active_variants().filter(stock__gt=0).exists()
        return self.in_stock

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

    @property
    def has_colour_variants(self):
        return self.variants.filter(active=True).exists()

    def active_variants(self):
        return self.variants.filter(active=True).select_related("colour").prefetch_related("images")

    def get_variant_by_colour_slug(self, colour_slug):
        """colour_slug matches Colour.name, case-insensitively, slug-normalized (spaces -> hyphens)."""
        if not colour_slug:
            return None
        normalized = colour_slug.replace("-", " ").strip().lower()
        return self.active_variants().filter(colour__name__iexact=normalized).first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]


class Colour(models.Model):
    """Site-wide colour palette. Admin-managed, reusable across products."""
    name = models.CharField(max_length=60, unique=True)
    hex_code = models.CharField(max_length=7, help_text="e.g. #000000")
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """A specific colour variant of a Product. One Product -> many ProductVariants."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    colour = models.ForeignKey(Colour, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                 help_text="Leave blank to use the product's base price.")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["product", "colour"], name="unique_product_colour"),
        ]

    def __str__(self):
        return f"{self.product.name} — {self.colour.name}"

    @property
    def effective_price(self):
        if self.discount_price:
            return self.discount_price
        if self.price:
            return self.price
        return self.product.effective_price

    @property
    def base_price(self):
        return self.price if self.price is not None else self.product.price

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def primary_image(self):
        return self.images.order_by("display_order", "id").first()


class VariantImage(models.Model):
    """An image belonging to exactly one ProductVariant (colour). Independent per colour."""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/variants/")
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "id"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            VariantImage.objects.filter(variant=self.variant).exclude(pk=self.pk).update(is_primary=False)
