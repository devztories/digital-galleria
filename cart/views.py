<<<<<<< HEAD
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    request.session['cart'] = cart

    return redirect('cart')


def cart(request):
    cart = request.session.get('cart', {})

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():

        product = get_object_or_404(Product, id=product_id)

        subtotal = product.price * quantity

        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return render(
        request,
        "cart/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        },
    )


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session["cart"] = cart

    return redirect("cart")


def update_cart(request, product_id):

    if request.method == "POST":

        quantity = int(request.POST.get("quantity", 1))

        cart = request.session.get("cart", {})

        product_id = str(product_id)

        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)

        request.session["cart"] = cart

    return redirect("cart")
=======
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.contrib.auth.decorators import login_required

from products.models import Product

from orders.models import ProductCustomization


# =========================================================
# CART DETAIL
#
# Supports:
#
# 1. Normal products
#
#    cart = {
#        "1": 2
#    }
#
# 2. Customized products
#
#    cart = {
#        "custom_5": {
#            "product_id": 1,
#            "quantity": 1,
#            "customization_id": 5
#        }
#    }
# =========================================================

def cart_detail(request):

    # =====================================================
    # GET SESSION CART
    # =====================================================

    cart = request.session.get(
        "cart",
        {}
    )


    cart_items = []

    total = 0


    # =====================================================
    # LOOP THROUGH CART
    # =====================================================

    for cart_key, cart_value in cart.items():

        # =================================================
        # CUSTOMIZED PRODUCT
        #
        # Customized products are stored as dictionaries.
        # =================================================

        if isinstance(
            cart_value,
            dict
        ):

            # ---------------------------------------------
            # GET PRODUCT ID
            # ---------------------------------------------

            product_id = cart_value.get(
                "product_id"
            )


            # ---------------------------------------------
            # GET QUANTITY
            # ---------------------------------------------

            quantity = cart_value.get(
                "quantity",
                1
            )


            # ---------------------------------------------
            # GET CUSTOMIZATION ID
            # ---------------------------------------------

            customization_id = cart_value.get(
                "customization_id"
            )


            # ---------------------------------------------
            # PRODUCT ID REQUIRED
            # ---------------------------------------------

            if not product_id:

                continue


            # ---------------------------------------------
            # GET PRODUCT
            # ---------------------------------------------

            try:

                product = Product.objects.get(
                    id=product_id
                )

            except Product.DoesNotExist:

                continue


            # ---------------------------------------------
            # GET CUSTOMIZATION
            # ---------------------------------------------

            customization = None


            if customization_id:

                customization_query = (

                    ProductCustomization.objects

                    .filter(

                        id=customization_id,

                        product=product,

                    )

                )


                # Security:
                # Logged-in customer should only see
                # their own customization.

                if request.user.is_authenticated:

                    customization_query = (

                        customization_query

                        .filter(
                            user=request.user
                        )

                    )


                customization = (

                    customization_query

                    .first()

                )


            # ---------------------------------------------
            # INVALID CUSTOMIZATION
            #
            # If cart says customized but the linked
            # customization no longer exists, skip item.
            # ---------------------------------------------

            if not customization:

                continue


            # ---------------------------------------------
            # QUANTITY SAFETY
            # ---------------------------------------------

            try:

                quantity = int(
                    quantity
                )

            except (
                ValueError,
                TypeError,
            ):

                quantity = 1


            if quantity < 1:

                quantity = 1


            # Do not display quantity above available stock.

            if product.stock > 0:

                quantity = min(

                    quantity,

                    product.stock,

                )


            # ---------------------------------------------
            # CALCULATE SUBTOTAL
            # ---------------------------------------------

            subtotal = (

                product.price

                *

                quantity

            )


            total += subtotal


            # ---------------------------------------------
            # ADD CART ITEM
            # ---------------------------------------------

            cart_items.append({

                "cart_key":
                    cart_key,

                "product":
                    product,

                "quantity":
                    quantity,

                "subtotal":
                    subtotal,

                "customization":
                    customization,

                "is_customized":
                    True,

            })


        # =================================================
        # NORMAL PRODUCT
        #
        # Example:
        #
        # "1": 2
        # =================================================

        else:

            try:

                # -----------------------------------------
                # PRODUCT ID
                # -----------------------------------------

                product_id = int(
                    cart_key
                )


                # -----------------------------------------
                # QUANTITY
                # -----------------------------------------

                quantity = int(
                    cart_value
                )


                # -----------------------------------------
                # GET PRODUCT
                # -----------------------------------------

                product = Product.objects.get(
                    id=product_id
                )


            except (
                Product.DoesNotExist,
                ValueError,
                TypeError,
            ):

                continue


            # ---------------------------------------------
            # QUANTITY SAFETY
            # ---------------------------------------------

            if quantity < 1:

                quantity = 1


            if product.stock > 0:

                quantity = min(

                    quantity,

                    product.stock,

                )


            # ---------------------------------------------
            # CALCULATE SUBTOTAL
            # ---------------------------------------------

            subtotal = (

                product.price

                *

                quantity

            )


            total += subtotal


            # ---------------------------------------------
            # ADD NORMAL ITEM
            # ---------------------------------------------

            cart_items.append({

                "cart_key":
                    cart_key,

                "product":
                    product,

                "quantity":
                    quantity,

                "subtotal":
                    subtotal,

                "customization":
                    None,

                "is_customized":
                    False,

            })


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "cart_items":
            cart_items,

        "total":
            total,

    }


    # =====================================================
    # RENDER CART
    # =====================================================

    return render(

        request,

        "cart.html",

        context,

    )


# =========================================================
# ADD NORMAL PRODUCT TO CART
# =========================================================

def add_to_cart(
    request,
    product_id
):

    # =====================================================
    # GET PRODUCT
    # =====================================================

    product = get_object_or_404(

        Product,

        id=product_id,

    )


    # =====================================================
    # CHECK STOCK
    # =====================================================

    if product.stock <= 0:

        return redirect(

            "product_detail",

            product_id=product.id,

        )


    # =====================================================
    # GET SESSION CART
    # =====================================================

    cart = request.session.get(

        "cart",

        {}

    )


    # Normal product key:
    #
    # "1"
    # "2"

    product_key = str(
        product.id
    )


    # =====================================================
    # GET REQUESTED QUANTITY
    # =====================================================

    try:

        requested_quantity = int(

            request.POST.get(

                "quantity",

                1

            )

        )

    except (
        ValueError,
        TypeError,
    ):

        requested_quantity = 1


    # =====================================================
    # MINIMUM QUANTITY
    # =====================================================

    if requested_quantity < 1:

        requested_quantity = 1


    # =====================================================
    # DO NOT EXCEED STOCK
    # =====================================================

    requested_quantity = min(

        requested_quantity,

        product.stock,

    )


    # =====================================================
    # PRODUCT ALREADY IN CART
    # =====================================================

    if product_key in cart:

        current_value = cart[
            product_key
        ]


        # ---------------------------------------------
        # NORMAL CART ITEM
        # ---------------------------------------------

        if not isinstance(
            current_value,
            dict
        ):

            try:

                current_quantity = int(
                    current_value
                )

            except (
                ValueError,
                TypeError,
            ):

                current_quantity = 0


            new_quantity = (

                current_quantity

                +

                requested_quantity

            )


            cart[
                product_key
            ] = min(

                new_quantity,

                product.stock,

            )


        # ---------------------------------------------
        # SAFETY FALLBACK
        # ---------------------------------------------

        else:

            cart[
                product_key
            ] = requested_quantity


    # =====================================================
    # NEW PRODUCT
    # =====================================================

    else:

        cart[
            product_key
        ] = requested_quantity


    # =====================================================
    # SAVE SESSION
    # =====================================================

    request.session[
        "cart"
    ] = cart


    request.session.modified = True


    # =====================================================
    # REDIRECT
    # =====================================================

    return redirect(
        "cart_detail"
    )


# =========================================================
# ADD CUSTOMIZED PRODUCT TO CART
#
# IMPORTANT:
#
# Every customization has a unique ID.
#
# Example:
#
# Product:
# Mug #1
#
# Customization #5:
# Photo A
#
# Customization #8:
# Photo B
#
# Cart:
#
# custom_5
# custom_8
#
# Therefore both designs remain separate.
# =========================================================

@login_required(login_url="login")
def add_customized_to_cart(
    request,
    product_id,
    customization_id
):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_customizable=True,
    )

    if product.stock <= 0:
        return redirect(
            "product_detail",
            product_id=product.id,
        )

    customization = get_object_or_404(
        ProductCustomization,
        id=customization_id,
        product=product,
        user=request.user,
        is_finalized=True,
    )

    # ==========================================
    # GET ORIGINAL SELECTED QUANTITY
    # ==========================================

    try:
        quantity = int(
            request.GET.get(
                "quantity",
                1
            )
        )
    except (ValueError, TypeError):
        quantity = 1

    quantity = max(quantity, 1)

    # Never exceed stock
    quantity = min(
        quantity,
        product.stock,
    )

    # Respect product maximum order quantity
    max_order_quantity = getattr(
        product,
        "max_order_quantity",
        0
    )

    if max_order_quantity:

        try:
            max_order_quantity = int(
                max_order_quantity
            )

            if max_order_quantity > 0:

                quantity = min(
                    quantity,
                    max_order_quantity,
                )

        except (ValueError, TypeError):
            pass

    # ==========================================
    # CART
    # ==========================================

    cart = request.session.get(
        "cart",
        {}
    )

    cart_key = (
        f"custom_{customization.id}"
    )

    # This customization is unique.
    # Store the ORIGINAL selected quantity.
    cart[cart_key] = {

        "product_id":
            product.id,

        "quantity":
            quantity,

        "customization_id":
            customization.id,

    }

    request.session["cart"] = cart

    request.session.modified = True

    return redirect(
        "cart_detail"
    )
    # =====================================================
    # GET CUSTOMIZABLE PRODUCT
    # =====================================================

    product = get_object_or_404(

        Product,

        id=product_id,

        is_customizable=True,

    )


    # =====================================================
    # CHECK STOCK
    # =====================================================

    if product.stock <= 0:

        return redirect(

            "product_detail",

            product_id=product.id,

        )


    # =====================================================
    # GET EXACT CUSTOMIZATION
    #
    # Security:
    #
    # - Must belong to this product
    # - Must belong to logged-in customer
    # - Must be finalized
    # =====================================================

    customization = get_object_or_404(

        ProductCustomization,

        id=customization_id,

        product=product,

        user=request.user,

        is_finalized=True,

    )


    # =====================================================
    # GET SESSION CART
    # =====================================================

    cart = request.session.get(

        "cart",

        {}

    )


    # =====================================================
    # UNIQUE CUSTOMIZED CART KEY
    #
    # Example:
    #
    # custom_5
    #
    # where 5 = customization ID
    # =====================================================

    cart_key = (

        f"custom_"

        f"{customization.id}"

    )


    # =====================================================
    # SAME CUSTOMIZATION ALREADY IN CART
    # =====================================================

    if cart_key in cart:

        cart_value = cart[
            cart_key
        ]


        if isinstance(
            cart_value,
            dict
        ):

            try:

                current_quantity = int(

                    cart_value.get(

                        "quantity",

                        1

                    )

                )

            except (
                ValueError,
                TypeError,
            ):

                current_quantity = 1


            # ---------------------------------------------
            # INCREASE QUANTITY
            #
            # Do not exceed stock.
            # ---------------------------------------------

            new_quantity = min(

                current_quantity + 1,

                product.stock,

            )


            cart_value[
                "quantity"
            ] = new_quantity


            cart[
                cart_key
            ] = cart_value


        # ---------------------------------------------
        # SAFETY FALLBACK
        # ---------------------------------------------

        else:

            cart[
                cart_key
            ] = {

                "product_id":
                    product.id,

                "quantity":
                    1,

                "customization_id":
                    customization.id,

            }


    # =====================================================
    # NEW CUSTOMIZED PRODUCT
    # =====================================================

    else:

        cart[
            cart_key
        ] = {

            "product_id":
                product.id,

            "quantity":
                1,

            "customization_id":
                customization.id,

        }


    # =====================================================
    # SAVE CART
    # =====================================================

    request.session[
        "cart"
    ] = cart


    request.session.modified = True


    # =====================================================
    # GO TO CART
    # =====================================================

    return redirect(
        "cart_detail"
    )


# =========================================================
# INCREASE QUANTITY
#
# Works for:
#
# Normal:
#
# "1": 2
#
# Customized:
#
# "custom_5": {
#     product_id: 1,
#     quantity: 2,
#     customization_id: 5
# }
# =========================================================

def increase_quantity(
    request,
    cart_key
):

    # =====================================================
    # GET CART
    # =====================================================

    cart = request.session.get(

        "cart",

        {}

    )


    cart_key = str(
        cart_key
    )


    # =====================================================
    # ITEM NOT FOUND
    # =====================================================

    if cart_key not in cart:

        return redirect(
            "cart_detail"
        )


    cart_value = cart[
        cart_key
    ]


    # =====================================================
    # CUSTOMIZED ITEM
    # =====================================================

    if isinstance(
        cart_value,
        dict
    ):

        product_id = cart_value.get(
            "product_id"
        )


        # ---------------------------------------------
        # PRODUCT
        # ---------------------------------------------

        product = get_object_or_404(

            Product,

            id=product_id,

        )


        # ---------------------------------------------
        # CURRENT QUANTITY
        # ---------------------------------------------

        try:

            quantity = int(

                cart_value.get(

                    "quantity",

                    1

                )

            )

        except (
            ValueError,
            TypeError,
        ):

            quantity = 1


        # ---------------------------------------------
        # INCREASE ONLY IF STOCK AVAILABLE
        # ---------------------------------------------

        if quantity < product.stock:

            cart_value[
                "quantity"
            ] = quantity + 1


        cart[
            cart_key
        ] = cart_value


    # =====================================================
    # NORMAL ITEM
    # =====================================================

    else:

        try:

            product = Product.objects.get(

                id=int(
                    cart_key
                )

            )


            quantity = int(
                cart_value
            )


            # ---------------------------------------------
            # CHECK STOCK
            # ---------------------------------------------

            if quantity < product.stock:

                cart[
                    cart_key
                ] = quantity + 1


        except (
            Product.DoesNotExist,
            ValueError,
            TypeError,
        ):

            pass


    # =====================================================
    # SAVE CART
    # =====================================================

    request.session[
        "cart"
    ] = cart


    request.session.modified = True


    return redirect(
        "cart_detail"
    )


# =========================================================
# DECREASE QUANTITY
#
# If quantity becomes zero:
#
# Item is removed from cart.
# =========================================================

def decrease_quantity(
    request,
    cart_key
):

    # =====================================================
    # GET CART
    # =====================================================

    cart = request.session.get(

        "cart",

        {}

    )


    cart_key = str(
        cart_key
    )


    # =====================================================
    # ITEM NOT FOUND
    # =====================================================

    if cart_key not in cart:

        return redirect(
            "cart_detail"
        )


    cart_value = cart[
        cart_key
    ]


    # =====================================================
    # CUSTOMIZED ITEM
    # =====================================================

    if isinstance(
        cart_value,
        dict
    ):

        try:

            quantity = int(

                cart_value.get(

                    "quantity",

                    1

                )

            )

        except (
            ValueError,
            TypeError,
        ):

            quantity = 1


        # ---------------------------------------------
        # DECREASE
        # ---------------------------------------------

        if quantity > 1:

            cart_value[
                "quantity"
            ] = quantity - 1


            cart[
                cart_key
            ] = cart_value


        # ---------------------------------------------
        # REMOVE
        # ---------------------------------------------

        else:

            del cart[
                cart_key
            ]


    # =====================================================
    # NORMAL ITEM
    # =====================================================

    else:

        try:

            quantity = int(
                cart_value
            )

        except (
            ValueError,
            TypeError,
        ):

            quantity = 1


        # ---------------------------------------------
        # DECREASE
        # ---------------------------------------------

        if quantity > 1:

            cart[
                cart_key
            ] = quantity - 1


        # ---------------------------------------------
        # REMOVE
        # ---------------------------------------------

        else:

            del cart[
                cart_key
            ]


    # =====================================================
    # SAVE CART
    # =====================================================

    request.session[
        "cart"
    ] = cart


    request.session.modified = True


    return redirect(
        "cart_detail"
    )


# =========================================================
# REMOVE FROM CART
#
# Works using exact cart key.
#
# Normal:
#
# 1
#
# Customized:
#
# custom_5
# =========================================================

def remove_from_cart(
    request,
    cart_key
):

    # =====================================================
    # GET CART
    # =====================================================

    cart = request.session.get(

        "cart",

        {}

    )


    cart_key = str(
        cart_key
    )


    # =====================================================
    # REMOVE ITEM
    # =====================================================

    if cart_key in cart:

        del cart[
            cart_key
        ]


    # =====================================================
    # SAVE CART
    # =====================================================

    request.session[
        "cart"
    ] = cart


    request.session.modified = True


    # =====================================================
    # REDIRECT
    # =====================================================

    return redirect(
        "cart_detail"
    )
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
