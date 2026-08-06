from django.db import models

from categories.models import Category


# =========================================================
# PRODUCT MODEL
# =========================================================

class Product(models.Model):


    # =====================================================
    # STOCK STATUS CHOICES
    # =====================================================

    STOCK_STATUS = [

        (
            "In Stock",
            "In Stock"
        ),

        (
            "Out of Stock",
            "Out of Stock"
        ),

    ]


    # =====================================================
    # CUSTOMER IMAGE UPLOAD MODE
    #
    # SINGLE:
    #
    # Customer uploads only one customization image.
    #
    #
    # MULTIPLE:
    #
    # Customer can upload multiple different images.
    #
    #
    # Example:
    #
    # Mug:
    #
    #       SINGLE
    #
    #
    # 20 Polaroids:
    #
    #       MULTIPLE
    #
    # =====================================================

    UPLOAD_MODE_CHOICES = [

        (
            "single",
            "Single Image"
        ),

        (
            "multiple",
            "Multiple Images"
        ),

    ]


    # =====================================================
    # PRODUCT NAME
    # =====================================================

    name = models.CharField(

        max_length=200

    )


    # =====================================================
    # CATEGORY
    # =====================================================

    category = models.ForeignKey(

        Category,

        on_delete=models.CASCADE,

        related_name="products",

    )


    # =====================================================
    # PRODUCT DESCRIPTION
    # =====================================================

    description = models.TextField()


    # =====================================================
    # PRODUCT PRICE
    #
    # IMPORTANT:
    #
    # This is ONLY the product price.
    #
    # Delivery charge is stored separately in:
    #
    #       delivery_charge
    #
    # Example:
    #
    # Product Price:
    #
    #       ₹500
    #
    # Delivery Charge:
    #
    #       ₹60
    #
    # Checkout:
    #
    #       Product Subtotal     ₹500
    #       Delivery Charge       ₹60
    #       -------------------------
    #       Total Payable        ₹560
    #
    # =====================================================

    price = models.DecimalField(

        max_digits=10,

        decimal_places=2,

    )


    # =====================================================
    # DELIVERY CHARGE
    #
    # Admin can configure a delivery charge separately
    # for every product.
    #
    #
    # Examples:
    #
    # Mug:
    #
    #       Product Price    = ₹299
    #       Delivery Charge  = ₹50
    #
    #
    # Photo Frame:
    #
    #       Product Price    = ₹799
    #       Delivery Charge  = ₹100
    #
    #
    # Digital / Free Delivery Product:
    #
    #       Delivery Charge  = ₹0
    #
    #
    # IMPORTANT:
    #
    # This field stores the delivery charge configured
    # for the product.
    #
    # Checkout/order calculation will use this field
    # server-side.
    #
    # Never trust a delivery charge sent from:
    #
    # - Browser
    # - JavaScript
    # - Hidden form fields
    # - Customer POST data
    #
    # The server should always calculate delivery charges
    # from Product.delivery_charge.
    #
    #
    # default=0.00:
    #
    # Existing products will safely receive ₹0 delivery
    # charge after migration until admin updates them.
    # =====================================================

    delivery_charge = models.DecimalField(

        max_digits=10,

        decimal_places=2,

        default=0.00,

        verbose_name="Delivery Charge",

        help_text=(

            "Delivery charge for this product. "
            "Enter 0 for free delivery."

        ),

    )


    # =====================================================
    # MAIN PRODUCT IMAGE
    #
    # This is the primary / cover image.
    #
    # Additional product images are stored separately
    # in ProductImage below.
    # =====================================================

    image = models.ImageField(

        upload_to="products/",

    )


    # =====================================================
    # STOCK QUANTITY
    # =====================================================

    stock = models.PositiveIntegerField(

        default=0

    )


    # =====================================================
    # STOCK STATUS
    # =====================================================

    stock_status = models.CharField(

        max_length=20,

        choices=STOCK_STATUS,

        default="In Stock",

    )


    # =====================================================
    # ORDER QUANTITY SETTINGS
    #
    # Example:
    #
    # Polaroid:
    #
    # Minimum quantity = 1
    #
    # Maximum quantity = 100
    #
    #
    # Customer cannot select more than max quantity.
    #
    #
    # max_order_quantity = 0 means:
    #
    # Use available stock as the limit.
    # =====================================================

    min_order_quantity = models.PositiveIntegerField(

        default=1,

        help_text=(

            "Minimum quantity a customer must order."

        ),

    )


    max_order_quantity = models.PositiveIntegerField(

        default=0,

        help_text=(

            "Maximum quantity allowed in one order. "
            "Enter 0 to use available stock as the limit."

        ),

    )


    # =====================================================
    # CUSTOMIZATION CONTROL
    # =====================================================

    is_customizable = models.BooleanField(

        default=True,

        help_text=(

            "Enable this option if customers "
            "are allowed to customize this product."

        ),

    )


    # =====================================================
    # CUSTOMER IMAGE UPLOAD MODE
    #
    # Determines whether customer can upload:
    #
    # - One image
    #
    # OR
    #
    # - Multiple different images
    # =====================================================

    customization_upload_mode = models.CharField(

        max_length=20,

        choices=UPLOAD_MODE_CHOICES,

        default="single",

        help_text=(

            "Choose Multiple Images for products such as "
            "Polaroids where customers may upload many photos."

        ),

    )


    # =====================================================
    # LIMIT MULTIPLE IMAGES BY QUANTITY
    #
    # TRUE:
    #
    # Quantity = 20
    #
    # Maximum uploaded images = 20
    #
    #
    # Quantity = 5
    #
    # Maximum uploaded images = 5
    #
    #
    # FALSE:
    #
    # max_customization_images is used instead.
    # =====================================================

    image_limit_based_on_quantity = models.BooleanField(

        default=True,

        help_text=(

            "If enabled, the maximum number of customer "
            "images equals the selected product quantity."

        ),

    )


    # =====================================================
    # MAXIMUM CUSTOMIZATION IMAGES
    #
    # Used when:
    #
    # image_limit_based_on_quantity = False
    #
    #
    # Example:
    #
    # max_customization_images = 10
    # =====================================================

    max_customization_images = models.PositiveIntegerField(

        default=1,

        help_text=(

            "Maximum customer images when the image limit "
            "is not based on product quantity."

        ),

    )


    # =====================================================
    # PRINT AREA X
    # =====================================================

    customization_x = models.FloatField(

        default=25,

        help_text=(

            "Print area horizontal starting position. "
            "Enter a percentage from 0 to 100."

        ),

    )


    # =====================================================
    # PRINT AREA Y
    # =====================================================

    customization_y = models.FloatField(

        default=25,

        help_text=(

            "Print area vertical starting position. "
            "Enter a percentage from 0 to 100."

        ),

    )


    # =====================================================
    # PRINT AREA WIDTH
    # =====================================================

    customization_width = models.FloatField(

        default=50,

        help_text=(

            "Width of the printable/customizable area "
            "as a percentage of the product image."

        ),

    )


    # =====================================================
    # PRINT AREA HEIGHT
    # =====================================================

    customization_height = models.FloatField(

        default=50,

        help_text=(

            "Height of the printable/customizable area "
            "as a percentage of the product image."

        ),

    )


    # =====================================================
    # CREATED DATE
    # =====================================================

    created_at = models.DateTimeField(

        auto_now_add=True

    )


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

            "name"

        ]


    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return self.name


# =========================================================
# PRODUCT GALLERY IMAGE MODEL
#
# One Product
#
#       |
#
#       +-- Main Image
#       |       Product.image
#       |
#       +-- ProductImage 1
#       |
#       +-- ProductImage 2
#       |
#       +-- ProductImage 3
#       |
#       +-- ProductImage 4
#       |
#       +-- ...
#
#
# Admin can upload multiple images of the same product
# from different angles.
# =========================================================

class ProductImage(models.Model):


    # =====================================================
    # PRODUCT
    # =====================================================

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name="gallery_images",

    )


    # =====================================================
    # ADDITIONAL IMAGE
    # =====================================================

    image = models.ImageField(

        upload_to="products/gallery/",

    )


    # =====================================================
    # DISPLAY ORDER
    #
    # 0 comes first
    #
    # then:
    #
    # 1
    # 2
    # 3
    # ...
    # =====================================================

    display_order = models.PositiveIntegerField(

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

            "display_order",

            "id",

        ]


    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return (

            f"{self.product.name} - "
            f"Gallery Image {self.id}"

        )