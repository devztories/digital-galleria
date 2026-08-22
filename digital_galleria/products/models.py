import json
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

    DELIVERY_PRICING_MODE_CHOICES = [
        ("site_default", "Use Site-wide Delivery Setting"),
        ("product", "Product Based (this product's own fixed fee below)"),
        ("count", "Count Based (tiered by how many of this product are ordered — Delivery → Count Rules)"),
    ]
    delivery_pricing_mode = models.CharField(
        max_length=20, choices=DELIVERY_PRICING_MODE_CHOICES, default="site_default",
        help_text=(
            "Decided here, when the product is added: how THIS product's delivery is charged. "
            "'Product Based' always uses this product's own First/Additional Item Delivery Charge "
            "below, regardless of the site-wide delivery mode. 'Count Based' always uses the site's "
            "Product Count delivery rules (Site Settings → Delivery → Count Rules), tiered by this "
            "product's own ordered quantity. Leave as 'Use Site-wide Delivery Setting' to follow "
            "whatever delivery mode Site Settings → Delivery is currently set to."
        ),
    )
    first_item_delivery_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    additional_item_delivery_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    # Kerala-aware, quantity-stepped delivery pricing. Used when Site Settings
    # → Delivery Mode is set to "Per-Product (Kerala / Outside Kerala)".
    # Each side (inside/outside Kerala) has its own base charge for the first
    # item, plus an "additional charge" applied every `qty_step` items beyond
    # the first (default step of 1 == every extra item).
    inside_kerala_delivery_charge = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        help_text="Base delivery charge for this product when the delivery address is in Kerala.",
    )
    inside_kerala_delivery_qty_step = models.PositiveIntegerField(
        default=1, help_text="Apply the additional Kerala delivery charge every this-many extra items.",
    )
    inside_kerala_delivery_additional_charge = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        help_text="Extra delivery charge per additional quantity step, inside Kerala.",
    )
    outside_kerala_delivery_charge = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        help_text="Base delivery charge for this product when the delivery address is outside Kerala.",
    )
    outside_kerala_delivery_qty_step = models.PositiveIntegerField(
        default=1, help_text="Apply the additional outside-Kerala delivery charge every this-many extra items.",
    )
    outside_kerala_delivery_additional_charge = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        help_text="Extra delivery charge per additional quantity step, outside Kerala.",
    )

    expected_delivery_days = models.PositiveIntegerField(
        default=0, blank=True,
        help_text="Number of days after the order date this product is expected to be delivered. "
                   "Leave as 0 to use the site-wide default set in Site Settings.",
    )

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
    preview_area_points = models.JSONField(
        default=list, blank=True,
        help_text=(
            "DEPRECATED — replaced by the per-image, multi-shape "
            "products.PreviewArea model. Kept only so old data isn't lost; "
            "no longer read or written by the customization flow. Use "
            "Admin → Products → Colour Variants → primary image → "
            "'Set preview shapes' instead."
        ),
    )

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

    @property
    def preview_images(self):
        """Every image of THIS colour that has at least one customization
        shape configured, in display order — not just the primary image.
        Admin can set shapes on any image for a colour (e.g. front + back
        views), and each becomes one page of the customer-facing preview
        gallery. Empty list if no image has shapes configured."""
        return [img for img in self.images.all() if img.preview_areas.exists()]

    @property
    def preview_areas(self):
        """All customization shapes across every preview-enabled image of
        this colour, flattened in (image order, then shape order). Kept as
        a flat list for callers that only need to match uploaded photos to
        shapes by overall position (1st upload -> 1st shape overall, etc.),
        regardless of which image that shape belongs to."""
        areas = []
        for img in self.preview_images:
            areas.extend(img.preview_areas.all())
        return areas


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

    @property
    def preview_areas_json(self):
        """JSON-encoded [{id, name, points}, ...] for this image's shapes —
        handed straight to the admin's multi-shape editor as a data
        attribute (Django templates can't safely serialize dicts to JSON
        themselves, since dict repr uses single quotes)."""
        return json.dumps([
            {"id": a.id, "name": a.name, "points": a.points}
            for a in self.preview_areas.all()
        ])


class PreviewArea(models.Model):
    """A single named shape (polygon) an admin has drawn on one VariantImage,
    marking a slot where a customer's uploaded photo should be shown as a
    live preview. A single image can carry SEVERAL of these — e.g. a
    multi-photo collage frame has one shape per photo slot — each tracked
    and positioned independently.
    """
    variant_image = models.ForeignKey(VariantImage, on_delete=models.CASCADE, related_name="preview_areas")
    name = models.CharField(
        max_length=60, blank=True,
        help_text="Optional label for this shape, e.g. 'Front', 'Left photo'. Shown to admin and, if set, to the customer.",
    )
    points = models.JSONField(
        help_text="Polygon points (list of [x_percent, y_percent], 0-100) relative to the variant image.",
    )
    display_order = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.name or f"Shape #{self.pk}"

    @property
    def points_json(self):
        return json.dumps(self.points)