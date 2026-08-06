<<<<<<< HEAD
from django.db import models
from django.contrib.auth.models import User
from store.models import Product


class PaymentSettings(models.Model):

    merchant_name = models.CharField(
        max_length=100
    )

    upi_id = models.CharField(
        max_length=100
    )

    qr_code = models.ImageField(
        upload_to="payment_qr/"
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True
    )

    instructions = models.TextField(
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return "Payment Settings"



class ProductCustomization(models.Model):

    FRAME_SIZES = [

        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),

    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # NEW FIELD
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customizations"
    )

    uploaded_photo = models.ImageField(
        upload_to="customer_uploads/"
    )

    custom_text = models.CharField(
        max_length=200,
        blank=True
    )

    font_name = models.CharField(
        max_length=100,
        default="Poppins"
    )

    frame_size = models.CharField(
        max_length=2,
        choices=FRAME_SIZES,
        default="M"
    )

    frame_color = models.CharField(
        max_length=50,
        default="Black"
    )

    notes = models.TextField(
        blank=True
    )
=======
from django.conf import settings
from django.db import models

from products.models import Product


# =========================================================
# CUSTOMIZATION
# =========================================================
#
# One customization represents one customer's customized
# version of a product.
#
# Example:
#
# Customer
#     |
#     +-- Product: Polaroid Prints
#     |
#     +-- Quantity: 20
#     |
#     +-- Customization
#             |
#             +-- Photo 1
#             +-- Photo 2
#             +-- Photo 3
#             +-- ...
#             +-- Photo 20
#
# =========================================================

class Customization(models.Model):

    # =====================================================
    # USER
    # =====================================================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customizations",
        null=True,
        blank=True,
    )


    # =====================================================
    # PRODUCT
    # =====================================================

    product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    related_name="customer_customizations",
    )

    # =====================================================
    # QUANTITY
    #
    # Example:
    #
    # Customer orders 20 Polaroids
    #
    # quantity = 20
    #
    # If the Product has:
    #
    # image_limit_based_on_quantity = True
    #
    # Customer can upload maximum 20 images.
    # =====================================================

    quantity = models.PositiveIntegerField(
        default=1
    )


    # =====================================================
    # LEGACY / SINGLE CUSTOMER IMAGE
    #
    # Keep this field for products that use only one image
    # and for compatibility with the existing customization
    # system.
    #
    # Multiple images are stored in CustomizationImage.
    # =====================================================

    uploaded_image = models.ImageField(
        upload_to="customizations/originals/",
        blank=True,
        null=True,
    )


    # =====================================================
    # CUSTOMIZATION DATA
    #
    # Can store optional customization information.
    #
    # Examples:
    #
    # {
    #     "text": "Happy Birthday",
    #     "font": "Arial"
    # }
    #
    # This keeps the model flexible for future products.
    # =====================================================

    customization_data = models.JSONField(
        default=dict,
        blank=True,
    )


    # =====================================================
    # CREATED DATE
    # =====================================================
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321

    created_at = models.DateTimeField(
        auto_now_add=True
    )

<<<<<<< HEAD
    def __str__(self):
        return f"{self.customer.username} - {self.product.name}"
=======

    # =====================================================
    # UPDATED DATE
    # =====================================================

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
            f"{self.product.name} - "
            f"Customization #{self.id}"
        )


    # =====================================================
    # MAXIMUM ALLOWED IMAGES
    # =====================================================

    @property
    def maximum_allowed_images(self):

        # ---------------------------------------------
        # SINGLE IMAGE PRODUCT
        # ---------------------------------------------

        if (
            self.product.customization_upload_mode
            == "single"
        ):

            return 1


        # ---------------------------------------------
        # LIMIT BASED ON QUANTITY
        #
        # Example:
        #
        # Quantity 20
        # Maximum images 20
        # ---------------------------------------------

        if self.product.image_limit_based_on_quantity:

            return max(
                self.quantity,
                1,
            )


        # ---------------------------------------------
        # ADMIN DEFINED LIMIT
        # ---------------------------------------------

        return max(
            self.product.max_customization_images,
            1,
        )


# =========================================================
# CUSTOMIZATION IMAGE
# =========================================================
#
# Stores EACH uploaded customer image separately.
#
#
# Example:
#
# Customization #10
#
#     CustomizationImage
#         position = 0
#         image = photo1.jpg
#
#     CustomizationImage
#         position = 1
#         image = photo2.jpg
#
#     CustomizationImage
#         position = 2
#         image = photo3.jpg
#
#
# This means there is NO fixed limit in the database.
#
# The allowed limit is controlled by the Product settings
# and validated by the backend.
#
# =========================================================

class CustomizationImage(models.Model):

    # =====================================================
    # CUSTOMIZATION
    # =====================================================

    customization = models.ForeignKey(
        Customization,
        on_delete=models.CASCADE,
        related_name="uploaded_images",
    )


    # =====================================================
    # ORIGINAL CUSTOMER IMAGE
    #
    # No preview image is required.
    #
    # Store the original uploaded file.
    # =====================================================

    image = models.ImageField(
        upload_to="customizations/images/",
    )


    # =====================================================
    # IMAGE POSITION
    #
    # Example:
    #
    # 0 = first photo
    # 1 = second photo
    # 2 = third photo
    #
    # This preserves customer upload order.
    # =====================================================

    position = models.PositiveIntegerField(
        default=0
    )


    # =====================================================
    # CREATED DATE
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
            f"{self.customization.product.name} - "
            f"Photo {self.position + 1}"
        )
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
