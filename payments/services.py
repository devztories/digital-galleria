from django.db import transaction

from products.models import Product

from .models import Payment


# =========================================================
# APPROVE PAYMENT
#
# PURPOSE:
#
# Customer submits:
#   UPI Transaction / UTR
#   Payment Screenshot
#
# Admin verifies payment.
#
# This service will:
#
#   1. Lock the payment
#   2. Validate payment proof
#   3. Validate order
#   4. Lock products
#   5. Validate stock
#   6. Reduce stock exactly once
#   7. Mark Payment = Paid
#   8. Mark Order payment_status = Paid
#   9. Confirm Pending order
#
# IMPORTANT:
#
# payment.stock_processed prevents stock from being
# deducted more than once.
# =========================================================


@transaction.atomic
def approve_payment(payment_id):

    # =====================================================
    # LOCK PAYMENT
    # =====================================================

    try:

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .get(
                id=payment_id
            )
        )

    except Payment.DoesNotExist:

        raise ValueError(
            "Payment record does not exist."
        )


    order = payment.order


    # =====================================================
    # VALIDATE ORDER
    # =====================================================

    if not order:

        raise ValueError(
            "This payment does not have a valid order."
        )


    # =====================================================
    # DO NOT APPROVE CANCELLED ORDER
    # =====================================================

    if order.status == "Cancelled":

        raise ValueError(
            "Cannot approve payment for a cancelled order."
        )


    # =====================================================
    # ALREADY PROCESSED
    #
    # This is extremely important.
    #
    # Example:
    #
    # Admin clicks Verify Payment twice.
    #
    # First click:
    #
    # stock 10
    #   ↓
    # stock 9
    #
    # stock_processed = True
    #
    #
    # Second click:
    #
    # We DO NOT reduce stock again.
    #
    # We only synchronize payment/order statuses.
    # =====================================================

    if payment.stock_processed:

        # =================================================
        # SYNCHRONIZE PAYMENT
        # =================================================

        payment_changed_fields = []


        if payment.status != "Paid":

            payment.status = "Paid"

            payment_changed_fields.append(
                "status"
            )


        if payment_changed_fields:

            payment_changed_fields.append(
                "updated_at"
            )

            payment.save(
                update_fields=
                payment_changed_fields
            )


        # =================================================
        # SYNCHRONIZE ORDER
        # =================================================

        order_changed_fields = []


        if order.payment_status != "Paid":

            order.payment_status = "Paid"

            order_changed_fields.append(
                "payment_status"
            )


        # Only Pending orders should automatically
        # become Confirmed.

        if order.status == "Pending":

            order.status = "Confirmed"

            order_changed_fields.append(
                "status"
            )


        if order_changed_fields:

            order_changed_fields.append(
                "updated_at"
            )

            order.save(
                update_fields=
                order_changed_fields
            )


        return payment


    # =====================================================
    # PAYMENT PROOF VALIDATION
    # =====================================================

    if not payment.upi_transaction_id:

        raise ValueError(
            "UPI Transaction / UTR ID is missing."
        )


    if not payment.payment_screenshot:

        raise ValueError(
            "Payment screenshot is missing."
        )


    # =====================================================
    # VALIDATE PAYMENT AMOUNT
    #
    # Payment amount should match order total.
    # =====================================================

    if payment.amount != order.total_amount:

        raise ValueError(

            (
                "Payment amount does not match "
                "the order total. "
                f"Payment amount: ₹{payment.amount}, "
                f"Order total: ₹{order.total_amount}."
            )

        )


    # =====================================================
    # GET ORDER ITEMS
    # =====================================================

    order_items = list(

        order.items
        .select_related(
            "product"
        )
        .all()

    )


    if not order_items:

        raise ValueError(
            "This order does not contain any items."
        )


    # =====================================================
    # CALCULATE REQUIRED PRODUCT QUANTITIES
    #
    # Same product may appear more than once.
    #
    # Example:
    #
    # Mug normal      x 2
    # Mug customized  x 1
    #
    # Total stock required = 3
    # =====================================================

    required_quantities = {}


    for item in order_items:

        # =================================================
        # PRODUCT MUST EXIST
        # =================================================

        if not item.product_id:

            raise ValueError(

                (
                    "The product linked to "
                    f"order item #{item.id} "
                    "no longer exists."
                )

            )


        # =================================================
        # QUANTITY MUST BE VALID
        # =================================================

        if item.quantity <= 0:

            raise ValueError(

                (
                    f"Invalid quantity for "
                    f"order item #{item.id}."
                )

            )


        required_quantities[
            item.product_id
        ] = (

            required_quantities.get(
                item.product_id,
                0
            )

            +

            item.quantity

        )


    # =====================================================
    # LOCK ALL REQUIRED PRODUCTS
    #
    # select_for_update prevents two payment approvals
    # from modifying the same product stock simultaneously.
    # =====================================================

    locked_products = {}


    for product_id in required_quantities:

        try:

            product = (

                Product.objects
                .select_for_update()
                .get(
                    id=product_id
                )

            )

        except Product.DoesNotExist:

            raise ValueError(

                (
                    f"Product #{product_id} "
                    "no longer exists."
                )

            )


        locked_products[
            product_id
        ] = product


    # =====================================================
    # VALIDATE STOCK
    #
    # IMPORTANT:
    #
    # Validate ALL products before changing ANY stock.
    #
    # Because this function is atomic, if anything fails,
    # the entire transaction rolls back.
    # =====================================================

    for (
        product_id,
        required_quantity
    ) in required_quantities.items():

        product = locked_products[
            product_id
        ]


        if product.stock < required_quantity:

            raise ValueError(

                (
                    f"Not enough stock for "
                    f"{product.name}. "
                    f"Required: {required_quantity}, "
                    f"Available: {product.stock}."
                )

            )


    # =====================================================
    # REDUCE STOCK
    #
    # Runs ONLY if:
    #
    # payment.stock_processed == False
    # =====================================================

    for (
        product_id,
        required_quantity
    ) in required_quantities.items():

        product = locked_products[
            product_id
        ]


        product.stock = (

            product.stock

            -

            required_quantity

        )


        product.save(

            update_fields=[
                "stock",
            ]

        )


    # =====================================================
    # MARK PAYMENT AS PAID
    #
    # IMPORTANT:
    #
    # stock_processed becomes True in the SAME database
    # transaction as stock deduction.
    #
    # Therefore:
    #
    # Stock cannot accidentally be processed twice.
    # =====================================================

    payment.status = "Paid"

    payment.stock_processed = True


    payment.save(

        update_fields=[

            "status",

            "stock_processed",

            "updated_at",

        ]

    )


    # =====================================================
    # UPDATE ORDER PAYMENT STATUS
    # =====================================================

    order.payment_status = "Paid"


    # =====================================================
    # AUTO CONFIRM ORDER
    #
    # Only:
    #
    # Pending
    #   ↓
    # Confirmed
    #
    # Never change:
    #
    # Processing
    # Shipped
    # Out for Delivery
    # Delivered
    #
    # back to Confirmed.
    # =====================================================

    if order.status == "Pending":

        order.status = "Confirmed"


    order.save(

        update_fields=[

            "payment_status",

            "status",

            "updated_at",

        ]

    )


    return payment


# =========================================================
# REJECT PAYMENT
#
# Used when:
#
# - Screenshot is invalid
# - UTR cannot be verified
# - Customer payment proof is incorrect
#
# IMPORTANT:
#
# A payment that already processed stock cannot be
# rejected using this function.
#
# Paid-order refunds use the separate refund workflow.
# =========================================================


@transaction.atomic
def reject_payment(payment_id):

    # =====================================================
    # LOCK PAYMENT
    # =====================================================

    try:

        payment = (

            Payment.objects
            .select_for_update()
            .select_related(
                "order"
            )
            .get(
                id=payment_id
            )

        )

    except Payment.DoesNotExist:

        raise ValueError(
            "Payment record does not exist."
        )


    order = payment.order


    # =====================================================
    # DO NOT REJECT PROCESSED PAYMENT
    #
    # If stock_processed == True:
    #
    # Payment was already approved.
    #
    # It must use:
    #
    # Cancellation
    #       ↓
    # Refund workflow
    #
    # instead.
    # =====================================================

    if payment.stock_processed:

        raise ValueError(

            (
                "This payment has already been approved "
                "and stock has already been processed. "
                "Use the cancellation/refund workflow instead."
            )

        )


    # =====================================================
    # DO NOT REJECT PAID PAYMENT
    # =====================================================

    if payment.status == "Paid":

        raise ValueError(

            (
                "A paid payment cannot be rejected directly. "
                "Use the cancellation/refund workflow instead."
            )

        )


    # =====================================================
    # MARK PAYMENT FAILED
    # =====================================================

    payment.status = "Failed"


    payment.save(

        update_fields=[

            "status",

            "updated_at",

        ]

    )


    # =====================================================
    # UPDATE ORDER PAYMENT STATUS
    # =====================================================

    order.payment_status = "Failed"


    order.save(

        update_fields=[

            "payment_status",

            "updated_at",

        ]

    )


    return payment


# =========================================================
# SYNCHRONIZE PAID ORDER
#
# PURPOSE:
#
# This helper can be used by Django Admin when an admin
# manually changes:
#
# Order.payment_status
#
# to:
#
# Paid
#
#
# Instead of simply saving "Paid", admin should call:
#
# synchronize_paid_order(order)
#
#
# This guarantees:
#
# Order payment_status = Paid
#
#           +
#
# Payment status = Paid
#
#           +
#
# Stock processed exactly once.
# =========================================================


@transaction.atomic
def synchronize_paid_order(order):

    # =====================================================
    # REFRESH / LOCK ORDER
    # =====================================================

    from orders.models import Order


    try:

        locked_order = (

            Order.objects
            .select_for_update()
            .get(
                id=order.id
            )

        )

    except Order.DoesNotExist:

        raise ValueError(
            "Order does not exist."
        )


    # =====================================================
    # CANCELLED ORDER
    # =====================================================

    if locked_order.status == "Cancelled":

        raise ValueError(

            (
                "A cancelled order cannot be "
                "manually marked as paid."
            )

        )


    # =====================================================
    # GET PAYMENT
    # =====================================================

    try:

        payment = locked_order.payment

    except Payment.DoesNotExist:

        raise ValueError(

            (
                f"Order #{locked_order.id} "
                "does not have a payment record."
            )

        )


    # =====================================================
    # APPROVE THROUGH SINGLE SAFE SERVICE
    # =====================================================

    return approve_payment(
        payment.id
    )