from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SiteSettings(models.Model):
    store_name = models.CharField(max_length=150, default="Digital Galleria")
    site_title = models.CharField(max_length=180, default="Digital Galleria", blank=True)
    logo = models.ImageField(upload_to="site/", blank=True, null=True)
    favicon = models.ImageField(upload_to="site/", blank=True, null=True)
    footer_logo = models.ImageField(upload_to="site/", blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    whatsapp_chat_url = models.URLField(max_length=500, blank=True, help_text="Direct WhatsApp chat link used by customer-facing buttons.")
    whatsapp_label = models.CharField(max_length=80, default="Customize via WhatsApp", blank=True)
    whatsapp_default_message = models.TextField(default="Hello Digital Galleria, I am sending customization images here.", blank=True)
    whatsapp_customization_enabled = models.BooleanField(default=True)
    whatsapp_include_order_number = models.BooleanField(default=True)
    whatsapp_include_product_name = models.BooleanField(default=True)
    whatsapp_include_customer_name = models.BooleanField(default=False)

    upi_id = models.CharField(max_length=100, blank=True)
    qr_code = models.ImageField(upload_to="site/", blank=True, null=True)
    payment_instructions = models.TextField(blank=True)
    payment_available = models.BooleanField(default=True)
    success_sound = models.FileField(upload_to="site/sounds/", blank=True, null=True)
    success_sound_enabled = models.BooleanField(default=True)

    low_stock_threshold = models.PositiveIntegerField(default=5)

    # Delivery configuration. Weight/count values are interpreted by the backend service.
    DELIVERY_MODE_CHOICES = [("weight", "Weight Based"), ("count", "Product Count Based")]
    delivery_mode = models.CharField(max_length=10, choices=DELIVERY_MODE_CHOICES, default="weight")
    cancellation_cutoff_status = models.CharField(
        max_length=12, choices=[("verified", "Verified"), ("processing", "Processing"), ("shipped", "Shipped")], default="processing"
    )

    # Customization upload controls.
    customization_enabled = models.BooleanField(default=True)
    customization_max_images = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(20)])
    customization_max_image_size_mb = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(50)])
    customization_allowed_formats = models.CharField(max_length=100, default="jpg,jpeg,png,webp", blank=True)

    class Meta:
        verbose_name_plural = "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.store_name


class ThemeSettings(models.Model):
    """Singleton global design tokens. Page overrides inherit from these values."""
    background = models.CharField(max_length=20, default="#111214")
    surface = models.CharField(max_length=20, default="#17181b")
    surface_alt = models.CharField(max_length=20, default="#202125")
    text = models.CharField(max_length=20, default="#f4f1e9")
    muted_text = models.CharField(max_length=20, default="#a5a5aa")
    heading = models.CharField(max_length=20, default="#ffffff")
    accent = models.CharField(max_length=20, default="#d9d4c7")
    button = models.CharField(max_length=20, default="#f4f1e9")
    button_text = models.CharField(max_length=20, default="#111214")
    button_hover = models.CharField(max_length=20, default="#d7d3c9")
    border = models.CharField(max_length=20, default="#34363a")
    input_background = models.CharField(max_length=20, default="#1b1c20")
    input_text = models.CharField(max_length=20, default="#f4f1e9")
    card = models.CharField(max_length=20, default="#17181b")
    header = models.CharField(max_length=20, default="#111214")
    footer = models.CharField(max_length=20, default="#0d0e10")
    search_background = models.CharField(max_length=20, default="#1b1c20")
    chatbot_background = models.CharField(max_length=20, default="#17181b")
    chatbot_surface = models.CharField(max_length=20, default="#202125")
    chatbot_text = models.CharField(max_length=20, default="#f4f1e9")
    chatbot_accent = models.CharField(max_length=20, default="#d9d4c7")
    success = models.CharField(max_length=20, default="#9eb59e")
    danger = models.CharField(max_length=20, default="#c58f8a")
    admin_background = models.CharField(max_length=20, default="#0f1012")
    admin_surface = models.CharField(max_length=20, default="#17181b")
    light_background = models.CharField(max_length=20, default="#f5f1e8")
    light_surface = models.CharField(max_length=20, default="#ffffff")
    light_text = models.CharField(max_length=20, default="#151619")
    light_muted_text = models.CharField(max_length=20, default="#66676b")
    light_border = models.CharField(max_length=20, default="#d9d5cd")
    default_animation_color_1 = models.CharField(max_length=20, default="#111214")
    default_animation_color_2 = models.CharField(max_length=20, default="#6d6e73")
    default_animation_color_3 = models.CharField(max_length=20, default="#f4f1e9")
    animation_enabled = models.BooleanField(default=True)
    animation_speed = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(5.0)])

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HeroSlide(models.Model):
    image = models.ImageField(upload_to="hero/")
    title = models.CharField(max_length=150, blank=True)
    subtitle = models.CharField(max_length=250, blank=True)
    link = models.CharField(max_length=250, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=5000)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title or f"Hero Slide #{self.pk}"


class Story(models.Model):
    image = models.ImageField(upload_to="stories/")
    duration_ms = models.PositiveIntegerField(default=4000)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Stories"
        ordering = ["display_order"]

    def __str__(self):
        return f"Story #{self.pk}"


class Advertisement(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="ads/")
    link = models.CharField(max_length=250, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    priority = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ["priority"]

    def __str__(self):
        return self.question


class Offer(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title


PAGE_KEYS = [
    ("home", "Homepage"), ("products_list", "Product Listing"), ("product_detail", "Product Details"),
    ("category", "Category"), ("search", "Search Results"), ("cart", "Cart"), ("checkout", "Checkout"),
    ("payment", "UPI Payment"), ("payment_success", "Payment Success"), ("orders", "Orders"),
    ("order_detail", "Order Details"), ("tracking", "Track Order"), ("cancel", "Cancel / Refund"),
    ("login", "Login"), ("register", "Register"), ("profile", "Profile"), ("wishlist", "Wishlist"),
    ("customization", "Customization"), ("empty", "Empty States"), ("error", "Error Pages"),
]


class PageTheme(models.Model):
    page_key = models.CharField(max_length=40, choices=PAGE_KEYS, unique=True)
    background = models.CharField(max_length=20, blank=True)
    surface = models.CharField(max_length=20, blank=True)
    text = models.CharField(max_length=20, blank=True)
    muted_text = models.CharField(max_length=20, blank=True)
    heading = models.CharField(max_length=20, blank=True)
    accent = models.CharField(max_length=20, blank=True)
    button = models.CharField(max_length=20, blank=True)
    button_text = models.CharField(max_length=20, blank=True)
    button_hover = models.CharField(max_length=20, blank=True)
    border = models.CharField(max_length=20, blank=True)
    input_background = models.CharField(max_length=20, blank=True)
    input_text = models.CharField(max_length=20, blank=True)
    card = models.CharField(max_length=20, blank=True)
    header = models.CharField(max_length=20, blank=True)
    footer = models.CharField(max_length=20, blank=True)
    search_background = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.get_page_key_display()


class AssetSetting(models.Model):
    KEY_CHOICES = [
        ("delivery_bike", "Delivery Tracking Bike"),
        ("delivery_scooter", "Delivery Tracking Scooter"),
        ("delivery_road", "Delivery Road"),
        ("empty_cart", "Empty Cart Illustration"),
        ("empty_wishlist", "Empty Wishlist Illustration"),
        ("empty_search", "No Search Results Illustration"),
        ("order_success", "Order Success Illustration"),
        ("refund", "Refund Illustration"),
        ("error", "Error Illustration"),
        ("chatbot_avatar", "Chatbot Avatar"),
        ("brand_circle", "Circular Brand Logo"),
    ]
    key = models.CharField(max_length=40, choices=KEY_CHOICES, unique=True)
    asset = models.FileField(upload_to="site/assets/", blank=True, null=True)
    enabled = models.BooleanField(default=True)
    alt_text = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.get_key_display()


class AnimationSettings(models.Model):
    key = models.CharField(max_length=40, unique=True, default="global")
    enabled = models.BooleanField(default=True)
    page_transitions = models.BooleanField(default=True)
    hover_effects = models.BooleanField(default=True)
    card_effects = models.BooleanField(default=True)
    search_effects = models.BooleanField(default=True)
    modal_effects = models.BooleanField(default=True)
    success_effects = models.BooleanField(default=True)
    tracking_effects = models.BooleanField(default=True)
    cancellation_effects = models.BooleanField(default=True)
    chatbot_effects = models.BooleanField(default=True)
    duration_ms = models.PositiveIntegerField(default=420, validators=[MinValueValidator(50), MaxValueValidator(3000)])
    intensity = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(2)])
    text_flow_enabled = models.BooleanField(default=True)
    text_flow_duration_ms = models.PositiveIntegerField(default=6500, validators=[MinValueValidator(1000), MaxValueValidator(20000)])
    text_flow_direction = models.CharField(max_length=20, default="90deg")
    tracking_speed = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(5)])
    bike_size_px = models.PositiveIntegerField(default=44, validators=[MinValueValidator(24), MaxValueValidator(100)])

    def save(self, *args, **kwargs):
        self.key = "global"
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(key="global")
        return obj
