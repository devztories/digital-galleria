"""
URL configuration for Digital Galleria project.

Main routes:

- Admin
- Home
- Product details
- Product customization
- Live product search suggestions
- Cart
- Orders
- Payments
- Accounts
"""

# =========================================================
# DJANGO IMPORTS
# =========================================================

from django.contrib import admin

from django.urls import (
    path,
    include,
)

from django.conf import settings

from django.conf.urls.static import static


# =========================================================
# PRODUCT VIEWS
# =========================================================

from products.views import (
    home,
    product_detail,
    customize_product,
    product_search_suggestions,
)


# =========================================================
# URL PATTERNS
# =========================================================

urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================

    path(
        "admin/",
        admin.site.urls,
    ),


    # =====================================================
    # HOME PAGE
    # =====================================================

    path(
        "",
        home,
        name="home",
    ),


    # =====================================================
    # LIVE PRODUCT SEARCH SUGGESTIONS
    #
    # Example:
    #
    # /search/suggestions/?q=photo
    #
    # Returns JSON used by JavaScript.
    # =====================================================

    path(
        "search/suggestions/",
        product_search_suggestions,
        name="product_search_suggestions",
    ),


    # =====================================================
    # PRODUCT DETAIL
    #
    # Example:
    #
    # /product/1/
    # =====================================================

    path(
        "product/<int:product_id>/",
        product_detail,
        name="product_detail",
    ),


    # =====================================================
    # PRODUCT CUSTOMIZATION
    #
    # Example:
    #
    # /product/1/customize/
    # =====================================================

    path(
        "product/<int:product_id>/customize/",
        customize_product,
        name="customize_product",
    ),


    # =====================================================
    # CART
    # =====================================================

    path(
        "cart/",
        include(
            "cart.urls"
        ),
    ),


    # =====================================================
    # ORDERS
    # =====================================================

    path(
        "orders/",
        include(
            "orders.urls"
        ),
    ),


    # =====================================================
    # PAYMENTS
    # =====================================================

    path(
        "payments/",
        include(
            "payments.urls"
        ),
    ),


    # =====================================================
    # ACCOUNTS
    # =====================================================

    path(
        "accounts/",
        include(
            "accounts.urls"
        ),
    ),

]


# =========================================================
# MEDIA FILES
#
# Development only.
#
# Allows Django development server to serve:
#
# - Product images
# - Profile images
# - Customization uploads
# - QR codes
# - Advertisement images
# etc.
# =========================================================

if settings.DEBUG:

    urlpatterns += static(

        settings.MEDIA_URL,

        document_root=
            settings.MEDIA_ROOT,

    )
