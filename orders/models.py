from django.db import models
<<<<<<< HEAD
from django.contrib.auth.models import User
from store.models import Product


class Order(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Rejected', 'Rejected'),
    ]

    PAYMENT_METHOD = [
        ('UPI', 'UPI'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    address = models.TextField()

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    pincode = models.CharField(max_length=10)

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Existing Order Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    # NEW PAYMENT FIELDS

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD,
        default="UPI"
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    payment_screenshot = models.ImageField(
        upload_to="payments/",
        blank=True,
        null=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name
=======
from django.conf import settings

from products.models import Product


# =========================================================
# ORDER
# =========================================================

class Order(models.Model):

    # =====================================================
    # ORDER STATUS
    # =====================================================

    STATUS_CHOICES = [

        (
            "Pending",
            "Pending"
        ),

        (
            "Confirmed",
            "Confirmed"
        ),

        (
            "Processing",
            "Processing"
        ),

        (
            "Cancellation Requested",
            "Cancellation Requested"
        ),

        (
            "Shipped",
            "Shipped"
        ),

        (
            "Out for Delivery",
            "Out for Delivery"
        ),

        (
            "Delivered",
            "Delivered"
        ),

        (
            "Cancelled",
            "Cancelled"
        ),

    ]


    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    PAYMENT_CHOICES = [

        (
            "ONLINE",
            "Online Payment"
        ),

    ]


    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    PAYMENT_STATUS_CHOICES = [

        (
            "Pending",
            "Pending"
        ),

        (
            "Paid",
            "Paid"
        ),

        (
            "Rejected",
            "Rejected"
        ),

        # Legacy compatibility
        (
            "Failed",
            "Failed"
        ),

    ]


    # =====================================================
    # CANCELLATION STATUS
    # =====================================================

    CANCELLATION_STATUS_CHOICES = [

        (
            "None",
            "None"
        ),

        (
            "Requested",
            "Requested"
        ),

        (
            "Approved",
            "Approved"
        ),

        (
            "Rejected",
            "Rejected"
        ),

    ]


    # =====================================================
    # REFUND STATUS
    # =====================================================

    REFUND_STATUS_CHOICES = [

        (
            "Not Required",
            "Not Required"
        ),

        (
            "Pending",
            "Pending"
        ),

        (
            "Refunded",
            "Refunded"
        ),

    ]


    # =====================================================
    # CUSTOMER ACCOUNT
    # =====================================================

    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="orders"

    )


    # =====================================================
    # CUSTOMER INFORMATION
    # =====================================================

    name = models.CharField(

        max_length=150

    )


    email = models.EmailField()


    phone = models.CharField(

        max_length=20

    )


    # =====================================================
    # SHIPPING ADDRESS
    # =====================================================

    address = models.TextField()


    city = models.CharField(

        max_length=100

    )


    state = models.CharField(

        max_length=100

    )


    postal_code = models.CharField(

        max_length=20

    )


    # =====================================================
    # ORIGINAL SUBTOTAL
    # =====================================================

    subtotal = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0

    )


    # =====================================================
    # COUPON CODE SNAPSHOT
    # =====================================================

    coupon_code = models.CharField(

        max_length=50,

        blank=True,

        default=""

    )


    # =====================================================
    # COUPON DISCOUNT PERCENTAGE SNAPSHOT
    # =====================================================

    coupon_discount_percentage = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=0

    )


    # =====================================================
    # DISCOUNT AMOUNT
    # =====================================================

    discount_amount = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0

    )


    # =====================================================
    # FINAL ORDER TOTAL
    # =====================================================

    total_amount = models.DecimalField(

        max_digits=10,

        decimal_places=2

    )


    # =====================================================
    # ORDER STATUS
    # =====================================================

    status = models.CharField(

        max_length=30,

        choices=STATUS_CHOICES,

        default="Pending"

    )


    # =====================================================
    # STATUS BEFORE CANCELLATION
    # =====================================================

    status_before_cancellation = models.CharField(

        max_length=30,

        blank=True,

        default=""

    )


    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    payment_method = models.CharField(

        max_length=20,

        choices=PAYMENT_CHOICES,

        default="ONLINE"

    )


    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    payment_status = models.CharField(

        max_length=20,

        choices=PAYMENT_STATUS_CHOICES,

        default="Pending"

    )


    # =====================================================
    # COURIER NAME
    # =====================================================

    courier_name = models.CharField(

        max_length=150,

        blank=True,

        default=""

    )


    # =====================================================
    # TRACKING ID
    # =====================================================

    tracking_id = models.CharField(

        max_length=150,

        blank=True,

        default=""

    )


    # =====================================================
    # EXPECTED DELIVERY DATE
    # =====================================================

    expected_delivery_date = models.DateField(

        blank=True,

        null=True

    )


    # =====================================================
    # DELIVERY NOTE
    # =====================================================

    delivery_note = models.TextField(

        blank=True,

        default=""

    )


    # =====================================================
    # CANCELLATION STATUS
    # =====================================================

    cancellation_status = models.CharField(

        max_length=30,

        choices=CANCELLATION_STATUS_CHOICES,

        default="None"

    )


    # =====================================================
    # CANCELLATION REASON
    # =====================================================

    cancellation_reason = models.TextField(

        blank=True,

        default=""

    )


    # =====================================================
    # CANCELLATION REQUEST TIME
    # =====================================================

    cancellation_requested_at = models.DateTimeField(

        blank=True,

        null=True

    )


    # =====================================================
    # REFUND STATUS
    # =====================================================

    refund_status = models.CharField(

        max_length=30,

        choices=REFUND_STATUS_CHOICES,

        default="Not Required"

    )


    # =====================================================
    # STOCK RESTORED
    # =====================================================

    stock_restored = models.BooleanField(

        default=False

    )


    # =====================================================
    # REFUND REFERENCE
    # =====================================================

    refund_reference = models.CharField(

        max_length=150,

        blank=True,

        default=""

    )


    # =====================================================
    # REFUND / CANCELLATION ADMIN NOTE
    # =====================================================

    cancellation_admin_note = models.TextField(

        blank=True,

        default=""

    )


    # =====================================================
    # REFUNDED TIME
    # =====================================================

    refunded_at = models.DateTimeField(

        blank=True,

        null=True

    )


    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(

        auto_now_add=True

    )


    updated_at = models.DateTimeField(

        auto_now=True

    )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = [

            "-created_at"

        ]


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return (

            f"Order #{self.id} - "
            f"{self.name}"

        )


# =========================================================
# PRODUCT CUSTOMIZATION
#
# TWO PHOTO SUBMISSION METHODS:
#
# 1. WEBSITE UPLOAD
#
# Customer uploads image(s) directly through website.
#
# Single image:
#
# original_image
#
# Multiple images:
#
# original_image = first image
#
# +
#
# ProductCustomizationImage = all uploaded images
#
#
# 2. WHATSAPP
#
# Customer clicks admin configured WhatsApp chat link.
#
# Customer manually sends photos through WhatsApp.
#
# Customer returns to website and confirms:
#
# "I have sent my photos via WhatsApp"
#
# No website image upload is required.
#
# =========================================================

class ProductCustomization(models.Model):


    # =====================================================
    # SUBMISSION METHOD CHOICES
    # =====================================================

    SUBMISSION_METHOD_CHOICES = [

        (
            "website",
            "Website Upload"
        ),

        (
            "whatsapp",
            "WhatsApp"
        ),

    ]


    # =====================================================
    # CUSTOMER
    # =====================================================

    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE,

        related_name="product_customizations",

        null=True,

        blank=True

    )


    # =====================================================
    # PRODUCT
    # =====================================================

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name="customizations",

        null=True,

        blank=True

    )


    # =====================================================
    # PHOTO SUBMISSION METHOD
    #
    # website:
    #
    # Customer uploads photos directly to website.
    #
    #
    # whatsapp:
    #
    # Customer sends photos using WhatsApp.
    #
    # =====================================================

    submission_method = models.CharField(

        max_length=20,

        choices=SUBMISSION_METHOD_CHOICES,

        default="website",

        db_index=True

    )


    # =====================================================
    # WHATSAPP PHOTOS CONFIRMED
    #
    # True only when customer checks:
    #
    # "I have sent my photos via WhatsApp"
    #
    # IMPORTANT:
    #
    # This is only CUSTOMER CONFIRMATION.
    #
    # It does NOT technically verify that admin actually
    # received the photos.
    #
    # =====================================================

    whatsapp_photos_confirmed = models.BooleanField(

        default=False

    )


    # =====================================================
    # ORIGINAL CUSTOMER IMAGE
    #
    # WEBSITE SINGLE IMAGE:
    #
    # Stores uploaded image.
    #
    #
    # WEBSITE MULTIPLE IMAGE:
    #
    # Stores first uploaded image for compatibility.
    #
    #
    # WHATSAPP:
    #
    # No website upload is required.
    #
    # Therefore this field MUST allow blank/null.
    #
    # =====================================================

    original_image = models.ImageField(

        upload_to="customizations/originals/",

        blank=True,

        null=True

    )


    # =====================================================
    # LEGACY PREVIEW IMAGE
    #
    # No longer used by new customization system.
    #
    # Retained for old database/order compatibility.
    # =====================================================

    preview_image = models.ImageField(

        upload_to="customizations/previews/",

        blank=True,

        null=True

    )


    # =====================================================
    # CUSTOMER INSTRUCTIONS
    # =====================================================

    instructions = models.TextField(

        blank=True

    )


    # =====================================================
    # LEGACY PREVIEW POSITION X
    # =====================================================

    position_x = models.FloatField(

        default=0

    )


    # =====================================================
    # LEGACY PREVIEW POSITION Y
    # =====================================================

    position_y = models.FloatField(

        default=0

    )


    # =====================================================
    # LEGACY PREVIEW SCALE
    # =====================================================

    scale = models.FloatField(

        default=1

    )


    # =====================================================
    # LEGACY PREVIEW ROTATION
    # =====================================================

    rotation = models.FloatField(

        default=0

    )


    # =====================================================
    # FINALIZED
    # =====================================================

    is_finalized = models.BooleanField(

        default=False

    )


    # =====================================================
    # CREATED TIME
    # =====================================================

    created_at = models.DateTimeField(

        auto_now_add=True

    )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = [

            "-created_at"

        ]


    # =====================================================
    # HELPER:
    # WEBSITE UPLOAD?
    # =====================================================

    @property
    def is_website_upload(self):

        return (

            self.submission_method
            == "website"

        )


    # =====================================================
    # HELPER:
    # WHATSAPP SUBMISSION?
    # =====================================================

    @property
    def is_whatsapp_submission(self):

        return (

            self.submission_method
            == "whatsapp"

        )


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        product_name = (

            self.product.name

            if self.product

            else "Unknown Product"

        )

        method = (

            self.get_submission_method_display()

            if self.submission_method

            else "Unknown Method"

        )

        return (

            f"Customization #{self.id} - "
            f"{product_name} - "
            f"{method}"

        )


# =========================================================
# ORDER ITEM
#
# Stores a snapshot of each purchased product.
# =========================================================

class OrderItem(models.Model):


    # =====================================================
    # ORDER
    # =====================================================

    order = models.ForeignKey(

        Order,

        on_delete=models.CASCADE,

        related_name="items"

    )


    # =====================================================
    # ORIGINAL PRODUCT
    # =====================================================

    product = models.ForeignKey(

        Product,

        on_delete=models.SET_NULL,

        null=True,

        blank=True

    )


    # =====================================================
    # PRODUCT NAME SNAPSHOT
    # =====================================================

    product_name = models.CharField(

        max_length=200

    )


    # =====================================================
    # PRICE SNAPSHOT
    # =====================================================

    price = models.DecimalField(

        max_digits=10,

        decimal_places=2

    )


    # =====================================================
    # QUANTITY
    # =====================================================

    quantity = models.PositiveIntegerField(

        default=1

    )


    # =====================================================
    # CUSTOMIZATION
    # =====================================================

    customization = models.ForeignKey(

        ProductCustomization,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="order_items"

    )


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return (

            f"{self.product_name} "
            f"x {self.quantity}"

        )


    # =====================================================
    # SUBTOTAL
    # =====================================================

    @property
    def subtotal(self):

        return (

            self.price

            *

            self.quantity

        )


# =========================================================
# PRODUCT CUSTOMIZATION IMAGE
#
# Stores multiple ORIGINAL customer images when:
#
# submission_method = website
#
#
# Example:
#
# ProductCustomization #10
#
#       |
#       +-- original_image = Photo 1
#       |
#       +-- uploaded_images
#               |
#               +-- Photo 1
#               +-- Photo 2
#               +-- Photo 3
#
#
# For WhatsApp submission:
#
# No ProductCustomizationImage objects are required.
#
# =========================================================

class ProductCustomizationImage(models.Model):


    # =====================================================
    # CUSTOMIZATION
    # =====================================================

    customization = models.ForeignKey(

        ProductCustomization,

        on_delete=models.CASCADE,

        related_name="uploaded_images"

    )


    # =====================================================
    # ORIGINAL CUSTOMER IMAGE
    # =====================================================

    image = models.ImageField(

        upload_to="customizations/multiple/"

    )


    # =====================================================
    # IMAGE POSITION
    # =====================================================

    position = models.PositiveIntegerField(

        default=0

    )


    # =====================================================
    # CREATED TIME
    # =====================================================

    created_at = models.DateTimeField(

        auto_now_add=True

    )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = [

            "position",

            "id",

        ]


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return (

            f"Customization "
            f"#{self.customization_id} "
            f"- Photo "
            f"{self.position + 1}"

        )
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
