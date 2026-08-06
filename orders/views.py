from decimal import Decimal

from django.utils import timezone
from django.contrib import messages

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.db import transaction

from django.contrib.auth.decorators import login_required

from django.http import JsonResponse

from django.views.decorators.http import require_POST


# =========================================================
# MODELS
# =========================================================

from products.models import Product

from coupons.models import Coupon

from accounts.models import Address

from .models import (
    Order,
    OrderItem,
    ProductCustomization,
)


# =========================================================
# HELPER: BUILD CART ITEMS
# =========================================================

def build_cart_items(request):

    cart = request.session.get(
        "cart",
        {}
    )

    cart_items = []

    total = Decimal(
        "0.00"
    )


    for cart_key, cart_value in list(
        cart.items()
    ):

        try:

            product_id = None

            quantity = 1

            customization_id = None


            # =================================================
            # OLD CART FORMAT
            #
            # "1": 2
            # =================================================

            if isinstance(
                cart_value,
                int
            ):

                product_id = int(
                    cart_key
                )

                quantity = int(
                    cart_value
                )


            # =================================================
            # NEW CART FORMAT
            # =================================================

            elif isinstance(
                cart_value,
                dict
            ):

                product_id = int(

                    cart_value.get(
                        "product_id"
                    )

                )

                quantity = int(

                    cart_value.get(
                        "quantity",
                        1
                    )

                )

                customization_id = (

                    cart_value.get(
                        "customization_id"
                    )

                )


            else:

                continue


            # =================================================
            # QUANTITY VALIDATION
            # =================================================

            if quantity <= 0:

                continue


            # =================================================
            # GET PRODUCT
            # =================================================

            product = (

                Product.objects

                .filter(
                    id=product_id
                )

                .first()

            )


            if product is None:

                continue


            # =================================================
            # GET CUSTOMIZATION
            # =================================================

            customization = None


            if customization_id:

                customization = (

                    ProductCustomization.objects

                    .filter(

                        id=customization_id,

                        product=product,

                    )

                    .first()

                )


                # =============================================
                # SECURITY
                #
                # Another user's customization cannot be used.
                # =============================================

                if customization:

                    customization_user_id = getattr(

                        customization,

                        "user_id",

                        None,

                    )


                    if (

                        customization_user_id

                        and

                        customization_user_id
                        !=
                        request.user.id

                    ):

                        customization = None


                if customization is None:

                    continue


            # =================================================
            # SUBTOTAL
            # =================================================

            item_subtotal = (

                product.price

                *

                quantity

            )


            total += item_subtotal


            cart_items.append(

                {

                    "cart_key":
                        cart_key,

                    "product":
                        product,

                    "quantity":
                        quantity,

                    "subtotal":
                        item_subtotal,

                    "customization":
                        customization,

                    "is_customized":
                        customization is not None,

                }

            )


        except (
            ValueError,
            TypeError,
        ):

            continue


    return (
        cart_items,
        total
    )


# =========================================================
# HELPER: CHECK ACTIVE COUPON
# =========================================================

def has_active_coupon():

    now = timezone.now()

    return Coupon.objects.filter(

        is_active=True,

        valid_from__lte=now,

        valid_until__gte=now,

    ).exists()


# =========================================================
# HELPER: VALIDATE COUPON
# =========================================================

def validate_coupon(
    coupon_code,
    subtotal
):

    subtotal = Decimal(
        str(subtotal)
    )


    coupon_code = (

        coupon_code

        or ""

    ).strip().upper()


    # =====================================================
    # EMPTY
    # =====================================================

    if not coupon_code:

        return {

            "valid":
                False,

            "coupon":
                None,

            "discount_amount":
                Decimal("0.00"),

            "final_total":
                subtotal,

            "message":
                "Please enter a coupon code.",

        }


    # =====================================================
    # FIND COUPON
    # =====================================================

    coupon = (

        Coupon.objects

        .filter(
            code__iexact=coupon_code
        )

        .first()

    )


    if coupon is None:

        return {

            "valid":
                False,

            "coupon":
                None,

            "discount_amount":
                Decimal("0.00"),

            "final_total":
                subtotal,

            "message":

                (
                    "Invalid coupon code. "
                    "Please enter a valid active coupon."
                ),

        }


    now = timezone.now()


    # =====================================================
    # DISABLED
    # =====================================================

    if not coupon.is_active:

        return {

            "valid":
                False,

            "coupon":
                None,

            "discount_amount":
                Decimal("0.00"),

            "final_total":
                subtotal,

            "message":

                (
                    "This coupon is currently unavailable."
                ),

        }


    # =====================================================
    # NOT STARTED
    # =====================================================

    if now < coupon.valid_from:

        return {

            "valid":
                False,

            "coupon":
                None,

            "discount_amount":
                Decimal("0.00"),

            "final_total":
                subtotal,

            "message":

                (
                    "This coupon is not active yet."
                ),

        }


    # =====================================================
    # EXPIRED
    # =====================================================

    if now > coupon.valid_until:

        return {

            "valid":
                False,

            "coupon":
                None,

            "discount_amount":
                Decimal("0.00"),

            "final_total":
                subtotal,

            "message":

                (
                    "This coupon has expired."
                ),

        }


    # =====================================================
    # MINIMUM ORDER
    # =====================================================

    minimum_amount = Decimal(

        str(

            coupon.minimum_order_amount

            or

            0

        )

    )


    if subtotal < minimum_amount:

        return {

            "valid":
                False,

            "coupon":
                None,

            "discount_amount":
                Decimal("0.00"),

            "final_total":
                subtotal,

            "message":

                (
                    f"This coupon requires a minimum "
                    f"order amount of "
                    f"₹{minimum_amount:.2f}."
                ),

        }


    # =====================================================
    # DISCOUNT
    # =====================================================

    discount_percentage = Decimal(

        str(
            coupon.discount_percentage
        )

    )


    discount_amount = (

        subtotal

        *

        discount_percentage

        /

        Decimal("100")

    ).quantize(

        Decimal("0.01")

    )


    if discount_amount > subtotal:

        discount_amount = subtotal


    final_total = (

        subtotal

        -

        discount_amount

    ).quantize(

        Decimal("0.01")

    )


    if final_total < 0:

        final_total = Decimal(
            "0.00"
        )


    return {

        "valid":
            True,

        "coupon":
            coupon,

        "discount_amount":
            discount_amount,

        "final_total":
            final_total,

        "message":

            (
                f"Coupon {coupon.code} "
                f"applied successfully. "
                f"You received "
                f"{coupon.discount_percentage}% OFF."
            ),

    }


# =========================================================
# AJAX APPLY COUPON
# =========================================================

@login_required(
    login_url="login"
)
@require_POST
def apply_coupon(request):

    (
        cart_items,
        subtotal

    ) = build_cart_items(
        request
    )


    if not cart_items:

        return JsonResponse(

            {

                "success":
                    False,

                "message":
                    "Your cart is empty.",

            },

            status=400,

        )


    coupon_code = (

        request.POST.get(
            "coupon_code",
            ""
        )

        .strip()

        .upper()

    )


    result = validate_coupon(

        coupon_code,

        subtotal,

    )


    if not result["valid"]:

        return JsonResponse(

            {

                "success":
                    False,

                "message":
                    result["message"],

                "subtotal":
                    f"{subtotal:.2f}",

                "discount_amount":
                    "0.00",

                "final_total":
                    f"{subtotal:.2f}",

            }

        )


    coupon = result[
        "coupon"
    ]


    return JsonResponse(

        {

            "success":
                True,

            "message":
                result["message"],

            "coupon_code":
                coupon.code,

            "discount_percentage":
                f"{coupon.discount_percentage}",

            "subtotal":
                f"{subtotal:.2f}",

            "discount_amount":
                f"{result['discount_amount']:.2f}",

            "final_total":
                f"{result['final_total']:.2f}",

        }

    )


# =========================================================
# CHECKOUT
#
# ADDRESS SYSTEM:
#
# Saved address exists:
#
#     Default address selected automatically
#
#     Customer can choose:
#
#     Use another address
#
#
# No saved address:
#
#     New address form displayed
#
#     Customer can save address
#
#
# IMPORTANT:
#
# Selected address is copied into Order.
#
# Therefore changing/deleting Address later
# will NOT modify old orders.
# =========================================================

@login_required(
    login_url="login"
)
def checkout(request):

    # =====================================================
    # CART
    # =====================================================

    cart = request.session.get(
        "cart",
        {}
    )


    if not cart:

        return redirect(
            "cart_detail"
        )


    (
        cart_items,
        subtotal

    ) = build_cart_items(
        request
    )


    if not cart_items:

        return redirect(
            "cart_detail"
        )


    # =====================================================
    # COUPON AVAILABILITY
    # =====================================================

    active_coupon_available = (

        has_active_coupon()

    )


    # =====================================================
    # SAVED ADDRESSES
    # =====================================================

    saved_addresses = (

        Address.objects

        .filter(
            user=request.user
        )

        .order_by(
            "-is_default",
            "-id"
        )

    )


    # =====================================================
    # DEFAULT ADDRESS
    # =====================================================

    default_address = (

        saved_addresses

        .filter(
            is_default=True
        )

        .first()

    )


    # =====================================================
    # FALLBACK
    #
    # Addresses exist but none marked default.
    # =====================================================

    if (

        default_address is None

        and

        saved_addresses.exists()

    ):

        default_address = (

            saved_addresses.first()

        )


    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    customer_name = (

        request.user.get_full_name()

        or

        request.user.username

    )


    customer_email = (

        getattr(
            request.user,
            "email",
            ""
        )

        or

        ""

    )


    customer_phone = (

        getattr(
            request.user,
            "phone",
            ""
        )

        or

        ""

    )


    # =====================================================
    # DEFAULT COUPON VALUES
    # =====================================================

    coupon_code = ""

    applied_coupon = None

    discount_amount = Decimal(
        "0.00"
    )

    final_total = subtotal

    coupon_message = ""

    coupon_error = ""


    # =====================================================
    # HELPER: CHECKOUT CONTEXT
    # =====================================================

    def get_checkout_context(
        **extra
    ):

        context = {

            "cart_items":
                cart_items,

            "saved_addresses":
                saved_addresses,

            "default_address":
                default_address,

            "has_saved_address":
                default_address is not None,

            "has_active_coupon":
                active_coupon_available,

            "subtotal":
                subtotal,

            "total":
                final_total,

            "discount_amount":
                discount_amount,

            "final_total":
                final_total,

            "coupon_code":
                coupon_code,

            "coupon_applied":
                applied_coupon is not None,

            "coupon_message":
                coupon_message,

            "coupon_error":
                coupon_error,

            "customer_name":
                customer_name,

            "customer_email":
                customer_email,

            "customer_phone":
                customer_phone,

            "use_another_address":
                False,

        }


        context.update(
            extra
        )


        return context


    # =====================================================
    # GET CHECKOUT
    # =====================================================

    if request.method == "GET":

        return render(

            request,

            "checkout.html",

            get_checkout_context(),

        )


    # =====================================================
    # POST
    #
    # USE ANOTHER ADDRESS?
    # =====================================================

    use_another_address = (

        request.POST.get(
            "use_another_address"
        )

        ==

        "on"

    )


    # =====================================================
    # NO SAVED ADDRESS
    #
    # Force new address mode.
    # =====================================================

    if default_address is None:

        use_another_address = True


    # =====================================================
    # EMAIL
    # =====================================================

    email = (

        request.POST.get(
            "email",
            ""
        )

        .strip()

        or

        customer_email

    )


    # =====================================================
    # DELIVERY VARIABLES
    # =====================================================

    name = ""

    phone = ""

    address_line1 = ""

    address_line2 = ""

    address = ""

    city = ""

    state = ""

    postal_code = ""


    # =====================================================
    # USE SAVED DEFAULT ADDRESS
    # =====================================================

    if (

        not use_another_address

        and

        default_address is not None

    ):

        name = (

            default_address
            .full_name
            .strip()

        )


        phone = (

            default_address
            .phone
            .strip()

        )


        address_line1 = (

            default_address
            .address_line1
            .strip()

        )


        address_line2 = (

            default_address
            .address_line2
            .strip()

            if default_address.address_line2

            else ""

        )


        address = ", ".join(

            part

            for part in [

                address_line1,

                address_line2,

            ]

            if part

        )


        city = (

            default_address
            .city
            .strip()

        )


        state = (

            default_address
            .state
            .strip()

        )


        postal_code = (

            default_address
            .pincode
            .strip()

        )


    # =====================================================
    # USE NEW / ANOTHER ADDRESS
    # =====================================================

    else:

        name = (

            request.POST.get(
                "name",
                ""
            )

            .strip()

        )


        phone = (

            request.POST.get(
                "phone",
                ""
            )

            .strip()

        )


        address_line1 = (

            request.POST.get(
                "address_line1",
                ""
            )

            .strip()

        )


        # =================================================
        # BACKWARD COMPATIBILITY
        #
        # If old checkout.html still sends "address",
        # accept that temporarily.
        # =================================================

        if not address_line1:

            address_line1 = (

                request.POST.get(
                    "address",
                    ""
                )

                .strip()

            )


        address_line2 = (

            request.POST.get(
                "address_line2",
                ""
            )

            .strip()

        )


        city = (

            request.POST.get(
                "city",
                ""
            )

            .strip()

        )


        state = (

            request.POST.get(
                "state",
                ""
            )

            .strip()

        )


        postal_code = (

            request.POST.get(
                "postal_code",
                ""
            )

            .strip()

        )


        address = ", ".join(

            part

            for part in [

                address_line1,

                address_line2,

            ]

            if part

        )


    # =====================================================
    # COUPON
    # =====================================================

    coupon_code = (

        request.POST.get(
            "coupon_code",
            ""
        )

        .strip()

        .upper()

    )


    if coupon_code:

        coupon_result = validate_coupon(

            coupon_code,

            subtotal,

        )


        if coupon_result["valid"]:

            applied_coupon = (

                coupon_result[
                    "coupon"
                ]

            )


            discount_amount = (

                coupon_result[
                    "discount_amount"
                ]

            )


            final_total = (

                coupon_result[
                    "final_total"
                ]

            )


            coupon_message = (

                coupon_result[
                    "message"
                ]

            )


        else:

            coupon_error = (

                coupon_result[
                    "message"
                ]

            )


            return render(

                request,

                "checkout.html",

                get_checkout_context(

                    customer_name=
                        name
                        or
                        customer_name,

                    customer_email=
                        email,

                    customer_phone=
                        phone
                        or
                        customer_phone,

                    address_line1=
                        address_line1,

                    address_line2=
                        address_line2,

                    city=
                        city,

                    state=
                        state,

                    postal_code=
                        postal_code,

                    use_another_address=
                        use_another_address,

                ),

            )


    # =====================================================
    # REQUIRED FIELDS
    # =====================================================

    if not all(

        [

            name,

            email,

            phone,

            address,

            city,

            state,

            postal_code,

        ]

    ):

        return render(

            request,

            "checkout.html",

            get_checkout_context(

                customer_name=
                    name
                    or
                    customer_name,

                customer_email=
                    email,

                customer_phone=
                    phone
                    or
                    customer_phone,

                address_line1=
                    address_line1,

                address_line2=
                    address_line2,

                city=
                    city,

                state=
                    state,

                postal_code=
                    postal_code,

                use_another_address=
                    use_another_address,

                error=

                    (
                        "Please fill in all "
                        "required delivery fields."
                    ),

            ),

        )


    # =====================================================
    # PHONE VALIDATION
    # =====================================================

    phone_for_validation = (

        phone

        .replace(
            " ",
            ""
        )

        .replace(
            "-",
            ""
        )

        .replace(
            "(",
            ""
        )

        .replace(
            ")",
            ""
        )

    )


    if phone_for_validation.startswith(
        "+"
    ):

        phone_digits = (

            phone_for_validation[1:]

        )

    else:

        phone_digits = (

            phone_for_validation

        )


    if (

        not phone_digits.isdigit()

        or

        len(phone_digits) < 10

        or

        len(phone_digits) > 15

    ):

        return render(

            request,

            "checkout.html",

            get_checkout_context(

                customer_name=
                    name,

                customer_email=
                    email,

                customer_phone=
                    phone,

                address_line1=
                    address_line1,

                address_line2=
                    address_line2,

                city=
                    city,

                state=
                    state,

                postal_code=
                    postal_code,

                use_another_address=
                    use_another_address,

                error=
                    "Enter a valid phone number.",

            ),

        )


    # =====================================================
    # PINCODE VALIDATION
    # =====================================================

    if (

        not postal_code.isdigit()

        or

        len(postal_code) != 6

    ):

        return render(

            request,

            "checkout.html",

            get_checkout_context(

                customer_name=
                    name,

                customer_email=
                    email,

                customer_phone=
                    phone,

                address_line1=
                    address_line1,

                address_line2=
                    address_line2,

                city=
                    city,

                state=
                    state,

                postal_code=
                    postal_code,

                use_another_address=
                    use_another_address,

                error=

                    (
                        "Please enter a valid "
                        "6-digit pincode."
                    ),

            ),

        )


    # =====================================================
    # SAVE NEW ADDRESS SETTINGS
    # =====================================================

    save_address = (

        request.POST.get(
            "save_address"
        )

        ==

        "on"

    )


    make_default = (

        request.POST.get(
            "make_default"
        )

        ==

        "on"

    )


    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    payment_method = "ONLINE"


    # =====================================================
    # CREATE ORDER
    # =====================================================

    try:

        with transaction.atomic():


            # =================================================
            # REBUILD CART
            # =================================================

            (
                fresh_cart_items,
                fresh_subtotal

            ) = build_cart_items(
                request
            )


            if not fresh_cart_items:

                return redirect(
                    "cart_detail"
                )


            # =================================================
            # REVALIDATE COUPON
            # =================================================

            applied_coupon = None

            discount_amount = Decimal(
                "0.00"
            )

            final_total = fresh_subtotal


            if coupon_code:

                coupon_result = validate_coupon(

                    coupon_code,

                    fresh_subtotal,

                )


                if not coupon_result[
                    "valid"
                ]:

                    return render(

                        request,

                        "checkout.html",

                        get_checkout_context(

                            cart_items=
                                fresh_cart_items,

                            subtotal=
                                fresh_subtotal,

                            total=
                                fresh_subtotal,

                            final_total=
                                fresh_subtotal,

                            discount_amount=
                                Decimal("0.00"),

                            coupon_applied=
                                False,

                            coupon_message=
                                "",

                            coupon_error=
                                coupon_result[
                                    "message"
                                ],

                            customer_name=
                                name,

                            customer_email=
                                email,

                            customer_phone=
                                phone,

                            address_line1=
                                address_line1,

                            address_line2=
                                address_line2,

                            city=
                                city,

                            state=
                                state,

                            postal_code=
                                postal_code,

                            use_another_address=
                                use_another_address,

                        ),

                    )


                applied_coupon = (

                    coupon_result[
                        "coupon"
                    ]

                )


                discount_amount = (

                    coupon_result[
                        "discount_amount"
                    ]

                )


                final_total = (

                    coupon_result[
                        "final_total"
                    ]

                )


            # =================================================
            # REQUESTED QUANTITY PER PRODUCT
            # =================================================

            requested_quantities = {}


            for item in fresh_cart_items:

                product_id = (

                    item[
                        "product"
                    ].id

                )


                requested_quantities[
                    product_id
                ] = (

                    requested_quantities.get(
                        product_id,
                        0
                    )

                    +

                    item[
                        "quantity"
                    ]

                )


            # =================================================
            # LOCK PRODUCTS
            # =================================================

            locked_products = {}


            for (
                product_id,
                requested_quantity
            ) in requested_quantities.items():


                product = (

                    Product.objects

                    .select_for_update()

                    .get(
                        id=product_id
                    )

                )


                locked_products[
                    product_id
                ] = product


                # =============================================
                # STOCK CHECK
                # =============================================

                if (

                    requested_quantity

                    >

                    product.stock

                ):

                    return render(

                        request,

                        "checkout.html",

                        get_checkout_context(

                            cart_items=
                                fresh_cart_items,

                            subtotal=
                                fresh_subtotal,

                            total=
                                final_total,

                            final_total=
                                final_total,

                            discount_amount=
                                discount_amount,

                            customer_name=
                                name,

                            customer_email=
                                email,

                            customer_phone=
                                phone,

                            address_line1=
                                address_line1,

                            address_line2=
                                address_line2,

                            city=
                                city,

                            state=
                                state,

                            postal_code=
                                postal_code,

                            use_another_address=
                                use_another_address,

                            error=

                                (
                                    f"Only "
                                    f"{product.stock} "
                                    f"units of "
                                    f"{product.name} "
                                    f"are currently available."
                                ),

                        ),

                    )


            # =================================================
            # SAVE NEW ADDRESS
            #
            # Only when customer is using another/new address.
            # =================================================

            if (

                use_another_address

                and

                save_address

            ):


                # =============================================
                # CHECK DUPLICATE
                # =============================================

                saved_address = (

                    Address.objects

                    .filter(

                        user=
                            request.user,

                        full_name__iexact=
                            name,

                        phone=
                            phone,

                        address_line1__iexact=
                            address_line1,

                        address_line2__iexact=
                            address_line2,

                        city__iexact=
                            city,

                        state__iexact=
                            state,

                        pincode=
                            postal_code,

                    )

                    .first()

                )


                # =============================================
                # CREATE IF NOT EXISTING
                # =============================================

                if saved_address is None:

                    saved_address = (

                        Address.objects.create(

                            user=
                                request.user,

                            address_type=

                                request.POST.get(
                                    "address_type",
                                    "home"
                                ),

                            full_name=
                                name,

                            phone=
                                phone,

                            address_line1=
                                address_line1,

                            address_line2=
                                address_line2,

                            city=
                                city,

                            state=
                                state,

                            pincode=
                                postal_code,

                            is_default=
                                False,

                        )

                    )


                # =============================================
                # FIRST ADDRESS AUTOMATICALLY DEFAULT
                #
                # OR CUSTOMER CHECKED MAKE DEFAULT
                # =============================================

                if (

                    default_address is None

                    or

                    make_default

                ):

                    saved_address.is_default = True

                    saved_address.save()


            # =================================================
            # COUPON SNAPSHOT
            # =================================================

            saved_coupon_code = ""

            saved_discount_percentage = Decimal(
                "0.00"
            )


            if applied_coupon:

                saved_coupon_code = (

                    applied_coupon.code

                )


                saved_discount_percentage = Decimal(

                    str(

                        applied_coupon
                        .discount_percentage

                    )

                )


            # =================================================
            # CREATE ORDER - FIXED VERSION
            # =================================================

            order = Order.objects.create(

                customer=request.user,          # ✅ ശരിയായി
                full_name=name,                 # ✅ ശരിയായി
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                pincode=postal_code,            # ✅ ശരിയായി
                subtotal=fresh_subtotal,
                coupon_code=saved_coupon_code,
                discount=discount_amount,       # ✅ ശരിയായി
                total_amount=final_total,
                status="Pending",               # ✅ ശരിയായി
                # payment_method ഫീൽഡ് ഇല്ല, അത് നീക്കി
                # payment_status ഫീൽഡ് ഇല്ല, അത് നീക്കി
                # coupon_discount_percentage ഫീൽഡ് ഇല്ല, അത് നീക്കി

            )


            # =================================================
            # CREATE ORDER ITEMS - FIXED VERSION
            # =================================================

            for item in fresh_cart_items:

                product = locked_products[

                    item[
                        "product"
                    ].id

                ]

                customization = item.get("customization")

                # OrderItem ഉണ്ടാക്കുക
                order_item = OrderItem.objects.create(

                    order=order,
                    product=product,
                    # product_name ഫീൽഡ് ഇല്ല, അത് നീക്കി
                    price=product.price,
                    quantity=item["quantity"],
                    # customization ഫീൽഡ് OrderItem-ൽ ഇല്ല, അത് നീക്കി

                )

                # =============================================
                # CUSTOMIZATION CONNECT
                # =============================================

                if customization:

                    customization.order_item = order_item

                    customization.save()


        # =====================================================
        # PAYMENT
        # =====================================================

        return redirect(

            "upi_payment",

            order_id=order.id,

        )


    # =========================================================
    # PRODUCT MISSING
    # =========================================================

    except Product.DoesNotExist:

        return render(

            request,

            "checkout.html",

            get_checkout_context(

                customer_name=
                    name,

                customer_email=
                    email,

                customer_phone=
                    phone,

                address_line1=
                    address_line1,

                address_line2=
                    address_line2,

                city=
                    city,

                state=
                    state,

                postal_code=
                    postal_code,

                use_another_address=
                    use_another_address,

                error=

                    (
                        "One of the products in your "
                        "cart is no longer available."
                    ),

            ),

        )


    # =========================================================
    # OTHER ERROR
    # =========================================================

    except Exception as error:

        print(

            "ORDER CREATION ERROR:",

            repr(error),

        )


        return render(

            request,

            "checkout.html",

            get_checkout_context(

                customer_name=
                    name,

                customer_email=
                    email,

                customer_phone=
                    phone,

                address_line1=
                    address_line1,

                address_line2=
                    address_line2,

                city=
                    city,

                state=
                    state,

                postal_code=
                    postal_code,

                use_another_address=
                    use_another_address,

                error=

                    (
                        "Unable to create your order. "
                        "Please try again."
                    ),

            ),

        )


# =========================================================
# ORDER CONFIRMATION
# =========================================================

@login_required(
    login_url="login"
)
def order_confirmation(
    request,
    order_id,
):

    order = get_object_or_404(

        Order,

        id=order_id,

        customer=request.user,    # user എന്നത് customer ആക്കി മാറ്റി

    )


    return render(

        request,

        "order_confirmation.html",

        {

            "order":
                order,

        },

    )


# =========================================================
# MY ORDERS
# =========================================================

@login_required(
    login_url="login"
)
def my_orders(request):

    orders = (

        Order.objects

        .filter(
            customer=request.user    # user എന്നത് customer ആക്കി മാറ്റി
        )

        .prefetch_related(

            "items",

            "items__product",

            "items__customization",

        )

        .order_by(
            "-created_at"
        )

    )


    return render(

        request,

        "my_orders.html",

        {

            "orders":
                orders,

        },

    )


# =========================================================
# ORDER DETAIL
# =========================================================

@login_required(
    login_url="login"
)
def order_detail(
    request,
    order_id,
):

    order = get_object_or_404(

        Order.objects

        .prefetch_related(

            "items",

            "items__product",

            "items__customization",

        ),

        id=order_id,

        customer=request.user,    # user എന്നത് customer ആക്കി മാറ്റി

    )


    order_items = (
        order.items.all()
    )


    # =====================================================
    # PAYMENT
    # =====================================================

    payment = None


    try:

        payment = (
            order.payment
        )


    except Exception:

        payment = None


    # =====================================================
    # CANCELLATION
    # =====================================================

    cancellable_statuses = [

        "Pending",

        "Confirmed",

        "Processing",

    ]


    can_cancel = (

        order.status
        in
        cancellable_statuses

        and

        order.cancellation_status
        !=
        "Requested"

    )


    return render(

        request,

        "order_detail.html",

        {

            "order":
                order,

            "order_items":
                order_items,

            "payment":
                payment,

            "can_cancel":
                can_cancel,

        },

    )


# =========================================================
# CANCEL ORDER
# =========================================================

@login_required(
    login_url="login"
)
def cancel_order(
    request,
    order_id,
):

    # =====================================================
    # GET USER ORDER
    # =====================================================

    order = get_object_or_404(

        Order,

        id=order_id,

        customer=request.user,    # user എന്നത് customer ആക്കി മാറ്റി

    )


    # =====================================================
    # POST ONLY
    # =====================================================

    if request.method != "POST":

        messages.error(

            request,

            "Invalid cancellation request.",

        )


        return redirect(

            "order_detail",

            order_id=order.id,

        )


    # =====================================================
    # REASON
    # =====================================================

    cancellation_reason = (

        request.POST.get(
            "cancellation_reason",
            ""
        )

        .strip()

    )


    additional_details = (

        request.POST.get(
            "additional_details",
            ""
        )

        .strip()

    )


    if not cancellation_reason:

        messages.error(

            request,

            (
                "Please select a "
                "cancellation reason."
            ),

        )


        return redirect(

            "order_detail",

            order_id=order.id,

        )


    # =====================================================
    # LIMIT SIZE
    # =====================================================

    cancellation_reason = (

        cancellation_reason[:500]

    )


    additional_details = (

        additional_details[:1000]

    )


    # =====================================================
    # FINAL REASON
    # =====================================================

    final_reason = (

        cancellation_reason

    )


    if additional_details:

        final_reason += (

            "\n\nAdditional details: "

            +

            additional_details

        )


    # =====================================================
    # PROCESS
    # =====================================================

    try:

        with transaction.atomic():


            order = (

                Order.objects

                .select_for_update()

                .get(

                    id=order_id,

                    customer=request.user,    # user എന്നത് customer ആക്കി മാറ്റി

                )

            )


            # =================================================
            # ALREADY REQUESTED
            # =================================================

            if (

                order.status
                ==
                "Cancellation Requested"

                or

                order.cancellation_status
                ==
                "Requested"

            ):

                messages.info(

                    request,

                    (
                        "Your cancellation request "
                        "is already waiting for review."
                    ),

                )


                return redirect(

                    "order_detail",

                    order_id=order.id,

                )


            # =================================================
            # ALREADY CANCELLED
            # =================================================

            if order.status == "Cancelled":

                messages.info(

                    request,

                    (
                        "This order is already cancelled."
                    ),

                )


                return redirect(

                    "order_detail",

                    order_id=order.id,

                )


            # =================================================
            # SHIPPING STARTED
            # =================================================

            blocked_statuses = [

                "Shipped",

                "Out for Delivery",

                "Delivered",

            ]


            if order.status in blocked_statuses:

                messages.error(

                    request,

                    (
                        "This order can no longer "
                        "be cancelled because shipping "
                        "has already started."
                    ),

                )


                return redirect(

                    "order_detail",

                    order_id=order.id,

                )


            # =================================================
            # ALLOWED
            # =================================================

            allowed_statuses = [

                "Pending",

                "Confirmed",

                "Processing",

            ]


            if order.status not in allowed_statuses:

                messages.error(

                    request,

                    (
                        "Cancellation is not "
                        "available for this order."
                    ),

                )


                return redirect(

                    "order_detail",

                    order_id=order.id,

                )


            # =================================================
            # SAVE PREVIOUS STATUS
            # =================================================

            previous_status = (

                order.status

            )


            order.status_before_cancellation = (

                previous_status

            )


            order.cancellation_reason = (

                final_reason

            )


            order.cancellation_requested_at = (

                timezone.now()

            )


            # =================================================
            # PAID ORDER
            # =================================================

            if order.payment_status == "Paid":

                order.status = (

                    "Cancellation Requested"

                )


                order.cancellation_status = (

                    "Requested"

                )


                order.refund_status = (

                    "Pending"

                )


                order.cancellation_admin_note = ""


                order.save(

                    update_fields=[

                        "status",

                        "status_before_cancellation",

                        "cancellation_status",

                        "cancellation_reason",

                        "cancellation_requested_at",

                        "cancellation_admin_note",

                        "refund_status",

                        "updated_at",

                    ]

                )


                messages.success(

                    request,

                    (
                        "Your cancellation request "
                        "has been submitted successfully. "
                        "It is waiting for admin review."
                    ),

                )


            # =================================================
            # UNPAID ORDER
            # =================================================

            else:

                order.status = (

                    "Cancelled"

                )


                order.cancellation_status = (

                    "Approved"

                )


                order.refund_status = (

                    "Not Required"

                )


                order.stock_restored = False


                order.cancellation_admin_note = ""


                order.save(

                    update_fields=[

                        "status",

                        "status_before_cancellation",

                        "cancellation_status",

                        "cancellation_reason",

                        "cancellation_requested_at",

                        "cancellation_admin_note",

                        "refund_status",

                        "stock_restored",

                        "updated_at",

                    ]

                )


                messages.success(

                    request,

                    (
                        "Your order has been "
                        "cancelled successfully."
                    ),

                )


    except Order.DoesNotExist:

        messages.error(

            request,

            "Order not found.",

        )


        return redirect(
            "my_orders"
        )


    except Exception as error:

        print(

            "CANCEL ORDER ERROR:",

            repr(error),

        )


        messages.error(

            request,

            (
                "Something went wrong while "
                "processing your cancellation. "
                "Please try again."
            ),

        )


        return redirect(

            "order_detail",

            order_id=order_id,

        )


    return redirect(

        "order_detail",

        order_id=order.id,

    )