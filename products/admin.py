from django.contrib import admin

from .models import (
    Product,
    ProductImage,
)


# =========================================================
# PRODUCT GALLERY IMAGE INLINE
# =========================================================
#
# Allows admin to upload multiple images for one product
# directly from the Product Add / Edit page.
#
#
# Example:
#
# Product:
#
#       Custom Mug
#
#
# Main Image:
#
#       Main product cover image
#
#
# Additional Images:
#
#       Front View
#       Side View
#       Back View
#       Close-up View
#
#
# Admin can click:
#
#       + Add another Product Image
#
# =========================================================

class ProductImageInline(admin.TabularInline):


    # =====================================================
    # MODEL
    # =====================================================

    model = ProductImage


    # =====================================================
    # DEFAULT EXTRA ROW
    # =====================================================

    extra = 1


    # =====================================================
    # FIELDS
    # =====================================================

    fields = (

        "image",

        "display_order",

    )


    # =====================================================
    # ORDERING
    # =====================================================

    ordering = (

        "display_order",

        "id",

    )


# =========================================================
# PRODUCT ADMIN
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):


    # =====================================================
    # PRODUCT LIST
    #
    # Delivery Charge is displayed separately from
    # Product Price.
    #
    #
    # Example:
    #
    # Name       Price       Delivery
    #
    # Mug        ₹299        ₹50
    #
    # Frame      ₹799        ₹100
    #
    # =====================================================

    list_display = (

        "name",

        "category",

        "price",

        "delivery_charge",

        "stock",

        "stock_status",

        "min_order_quantity",

        "max_order_quantity",

        "is_customizable",

        "customization_upload_mode",

        "updated_at",

    )


    # =====================================================
    # PRODUCT LIST LINKS
    #
    # Product name can always be clicked to edit.
    # =====================================================

    list_display_links = (

        "name",

    )


    # =====================================================
    # FILTERS
    # =====================================================

    list_filter = (

        "category",

        "stock_status",

        "is_customizable",

        "customization_upload_mode",

        "image_limit_based_on_quantity",

        "created_at",

    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_fields = (

        "name",

        "description",

        "category__name",

    )


    # =====================================================
    # ORDERING
    # =====================================================

    ordering = (

        "name",

    )


    # =====================================================
    # READ ONLY
    # =====================================================

    readonly_fields = (

        "created_at",

        "updated_at",

    )


    # =====================================================
    # MULTIPLE PRODUCT IMAGES
    # =====================================================

    inlines = [

        ProductImageInline,

    ]


    # =====================================================
    # ADMIN FORM SECTIONS
    # =====================================================

    fieldsets = (


        # -------------------------------------------------
        # GENERAL INFORMATION
        # -------------------------------------------------

        (
            "General Information",

            {

                "fields": (

                    "name",

                    "category",

                    "description",

                    "image",

                ),

                "description": (

                    "Enter the basic product information "
                    "and upload the main product image."

                ),

            },

        ),


        # -------------------------------------------------
        # PRICING AND DELIVERY
        #
        # Product price and delivery charge are stored
        # separately.
        #
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
        #
        # Checkout:
        #
        #       Product Subtotal      ₹500
        #
        #       Delivery Charge        ₹60
        #
        #       --------------------------
        #
        #       Total Payable         ₹560
        #
        #
        # IMPORTANT:
        #
        # Delivery charge = 0
        #
        # means:
        #
        #       FREE DELIVERY
        #
        # -------------------------------------------------

        (
            "Pricing & Delivery",

            {

                "fields": (

                    "price",

                    "delivery_charge",

                ),

                "description": (

                    "Set the product selling price and "
                    "delivery charge separately. "
                    "Enter 0 in Delivery Charge if this "
                    "product has free delivery. "
                    "The delivery charge will later be "
                    "added automatically to the customer's "
                    "checkout total."

                ),

            },

        ),


        # -------------------------------------------------
        # STOCK MANAGEMENT
        # -------------------------------------------------

        (
            "Stock Management",

            {

                "fields": (

                    "stock",

                    "stock_status",

                ),

                "description": (

                    "Manage available product stock and "
                    "the current stock status."

                ),

            },

        ),


        # -------------------------------------------------
        # ORDER QUANTITY SETTINGS
        # -------------------------------------------------

        (
            "Order Quantity Settings",

            {

                "fields": (

                    "min_order_quantity",

                    "max_order_quantity",

                ),

                "description": (

                    "Control how many units of this product "
                    "a customer can order. "
                    "Set Maximum Order Quantity to 0 to use "
                    "available stock as the maximum limit."

                ),

            },

        ),


        # -------------------------------------------------
        # CUSTOMER IMAGE UPLOAD SETTINGS
        # -------------------------------------------------

        (
            "Customer Image Upload Settings",

            {

                "fields": (

                    "customization_upload_mode",

                    "image_limit_based_on_quantity",

                    "max_customization_images",

                ),

                "description": (

                    "For products such as Polaroid prints, "
                    "choose Multiple Images. "
                    "If Image Limit Based On Quantity is "
                    "enabled, a customer ordering 20 units "
                    "can upload up to 20 different images."

                ),

            },

        ),


        # -------------------------------------------------
        # CUSTOMIZATION / PRINT AREA
        # -------------------------------------------------

        (
            "Customization Settings",

            {

                "fields": (

                    "is_customizable",

                    "customization_x",

                    "customization_y",

                    "customization_width",

                    "customization_height",

                ),

                "description": (

                    "For customizable products, use the "
                    "visual editor shown below these fields "
                    "to position and resize the print area. "
                    "The X, Y, Width and Height percentages "
                    "will update automatically."

                ),

            },

        ),


        # -------------------------------------------------
        # SYSTEM INFORMATION
        # -------------------------------------------------

        (
            "System Information",

            {

                "fields": (

                    "created_at",

                    "updated_at",

                ),

                "classes": (

                    "collapse",

                ),

            },

        ),

    )


    # =====================================================
    # ITEMS PER PAGE
    # =====================================================

    list_per_page = 25


    # =====================================================
    # LOAD CUSTOM ADMIN FILES
    #
    # Existing visual print-area editor is preserved.
    # =====================================================

    class Media:

        css = {

            "all": (

                "products/admin/product_print_area.css",

            )

        }

        js = (

            "products/admin/product_print_area.js",

        )


# =========================================================
# PRODUCT IMAGE ADMIN
#
# Product images can primarily be managed inside Product.
#
# This separate admin is useful for:
#
# - Searching gallery images
# - Editing gallery images
# - Changing display order
#
# =========================================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):


    # =====================================================
    # LIST DISPLAY
    # =====================================================

    list_display = (

        "id",

        "product",

        "display_order",

        "created_at",

    )


    # =====================================================
    # LIST DISPLAY LINKS
    # =====================================================

    list_display_links = (

        "id",

        "product",

    )


    # =====================================================
    # FILTERS
    # =====================================================

    list_filter = (

        "created_at",

    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_fields = (

        "product__name",

    )


    # =====================================================
    # ORDERING
    # =====================================================

    ordering = (

        "product",

        "display_order",

        "id",

    )


    # =====================================================
    # ITEMS PER PAGE
    # =====================================================

    list_per_page = 50