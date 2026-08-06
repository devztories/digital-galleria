from urllib.parse import urlencode

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.contrib.auth.decorators import login_required

from django.db import (
    transaction,
    IntegrityError,
)

from django.utils import timezone


# =========================================================
# MODELS
# =========================================================

from orders.models import Order

from .models import (
    Payment,
    PaymentSettings,
)


# =========================================================
# HELPER - GET CURRENT PAYMENT SETTINGS
#
# Gets the most recently updated UPI payment configuration.
# =========================================================

def get_payment_settings():

    return (

        PaymentSettings.objects

        .order_by(
            "-updated_at"
        )

        .first()

    )


# =========================================================
# HELPER - BUILD UPI PAYMENT LINK
#
# FINAL TEST FLOW:
#
# Customer clicks:
#
#       Open UPI App
#
#           ↓
#
# Phone/browser opens a supported installed UPI app.
#
#           ↓
#
# We send:
#
# - Personal UPI ID
# - UPI Receiver Name
# - Exact Order Amount
# - INR Currency
# - Order Reference
#
#
# Example:
#
# upi://pay?
# pa=example@oksbi
# &pn=Receiver Name
# &am=500.00
# &cu=INR
# &tn=Digital Galleria Order #5
#
#
# IMPORTANT:
#
# Amount ALWAYS comes from:
#
#       order.total_amount
#
# Never from:
#
# - Customer input
# - POST data
# - GET data
# - JavaScript
#
#
# SUPPORTED APP BEHAVIOUR:
#
# If the selected UPI app supports the standard deep-link
# parameters, the exact order amount should be pre-filled.
#
# Some UPI apps / browsers / devices may behave differently.
#
# Therefore customer must always verify:
#
# - Receiver
# - UPI ID
# - Amount
#
# before confirming payment.
# =========================================================

def build_upi_payment_link(
    order,
    payment_settings,
):

    # =====================================================
    # PAYMENT SETTINGS REQUIRED
    # =====================================================

    if not payment_settings:

        return ""


    # =====================================================
    # GET UPI ID
    # =====================================================

    upi_id = (

        payment_settings.upi_id

        or ""

    ).strip()


    # =====================================================
    # UPI ID REQUIRED
    # =====================================================

    if not upi_id:

        return ""


    # =====================================================
    # GET UPI RECEIVER NAME
    #
    # Preferred/new field:
    #
    #       upi_receiver_name
    #
    # Old field fallback:
    #
    #       business_name
    #
    # This fallback allows the view to work while migrating
    # from the old Business Name field to the new personal
    # UPI Receiver Name field.
    #
    # IMPORTANT:
    #
    # We DO NOT automatically force:
    #
    #       Digital Galleria
    #
    # as the receiver name.
    #
    # If a personal UPI ID is being used, pn should use the
    # corresponding receiver/payee name configured by admin.
    # =====================================================

    receiver_name = (

        getattr(
            payment_settings,
            "upi_receiver_name",
            "",
        )

        or

        getattr(
            payment_settings,
            "business_name",
            "",
        )

        or

        ""

    ).strip()


    # =====================================================
    # EXACT ORDER AMOUNT
    #
    # Always generated from server-side order data.
    #
    # Example:
    #
    # Decimal("500.00")
    #
    # becomes:
    #
    # "500.00"
    # =====================================================

    amount = (

        f"{order.total_amount:.2f}"

    )


    # =====================================================
    # UPI PARAMETERS
    #
    # pa
    # =
    # Payee Address / UPI ID
    #
    # pn
    # =
    # Payee / Receiver Name
    #
    # am
    # =
    # Exact Amount
    #
    # cu
    # =
    # Currency
    #
    # tn
    # =
    # Transaction Note
    # =====================================================

    parameters = {

        "pa":
            upi_id,

        "am":
            amount,

        "cu":
            "INR",

        "tn":
            f"Digital Galleria Order #{order.id}",

    }


    # =====================================================
    # ADD RECEIVER NAME
    #
    # Only add pn when admin has configured a name.
    # =====================================================

    if receiver_name:

        parameters["pn"] = (

            receiver_name

        )


    # =====================================================
    # BUILD UPI DEEP LINK
    # =====================================================

    return (

        "upi://pay?"

        +

        urlencode(
            parameters
        )

    )


# =========================================================
# HELPER - PAYMENT PAGE CONTEXT
#
# Centralized context builder.
#
# Used for:
#
# - Normal GET page
# - Validation errors
# - Duplicate UTR errors
# - Payment configuration errors
# =========================================================

def payment_page_context(
    order,
    payment,
    payment_settings,
    error=None,
):

    # =====================================================
    # BUILD UPI LINK
    #
    # Includes:
    #
    # - UPI ID
    # - Receiver Name
    # - Exact Order Amount
    # - INR
    # - Order Reference
    # =====================================================

    upi_payment_link = (

        build_upi_payment_link(

            order,

            payment_settings,

        )

    )


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        # -------------------------------------------------
        # ORDER
        # -------------------------------------------------

        "order":
            order,


        # -------------------------------------------------
        # PAYMENT
        # -------------------------------------------------

        "payment":
            payment,


        # -------------------------------------------------
        # ADMIN PAYMENT SETTINGS
        # -------------------------------------------------

        "payment_settings":
            payment_settings,


        # -------------------------------------------------
        # UPI DEEP LINK
        # -------------------------------------------------

        "upi_payment_link":
            upi_payment_link,

    }


    # =====================================================
    # OPTIONAL ERROR MESSAGE
    # =====================================================

    if error:

        context["error"] = (

            error

        )


    return context


# =========================================================
# HELPER - NORMALIZE UTR
#
# Example:
#
# "  abc 123  "
#
# becomes:
#
# "ABC123"
# =========================================================

def normalize_utr(
    utr
):

    return (

        str(
            utr or ""
        )

        .strip()

        .replace(
            " ",
            ""
        )

        .upper()

    )


# =========================================================
# HELPER - VALIDATE UTR
#
# UTR formats can differ between:
#
# - Banks
# - Google Pay
# - PhonePe
# - Paytm
# - BHIM
# - Other UPI applications
#
# Therefore validation should not be unnecessarily strict.
# =========================================================

def validate_utr(
    utr
):

    # =====================================================
    # REQUIRED
    # =====================================================

    if not utr:

        return (

            "Please enter your UPI "
            "Transaction / UTR number."

        )


    # =====================================================
    # MINIMUM LENGTH
    # =====================================================

    if len(utr) < 6:

        return (

            "Please enter a valid "
            "Transaction / UTR number."

        )


    # =====================================================
    # MAXIMUM LENGTH
    # =====================================================

    if len(utr) > 100:

        return (

            "The Transaction / UTR number "
            "is too long."

        )


    # =====================================================
    # ALLOWED SPECIAL CHARACTERS
    #
    # Different UPI apps/banks may use:
    #
    # -
    # /
    #
    # So validation should not be too strict.
    # =====================================================

    allowed_special_characters = {

        "-",

        "/",

    }


    # =====================================================
    # VALIDATE CHARACTERS
    # =====================================================

    for character in utr:

        if (

            not character.isalnum()

            and

            character
            not in
            allowed_special_characters

        ):

            return (

                "The Transaction / UTR number "
                "contains invalid characters."

            )


    # =====================================================
    # VALID
    # =====================================================

    return None


# =========================================================
# UPI PAYMENT PAGE
#
# FINAL FLOW:
#
# Order Created
#
#       ↓
#
# UPI Payment Page
#
#       ↓
#
# Customer sees exact order amount
#
#       ↓
#
# OPTION 1:
#
# Open UPI App
#
#       ↓
#
# Website sends:
#
# - Personal UPI ID
# - Receiver Name
# - Exact Order Amount
#
#       ↓
#
# Supported UPI app should pre-fill amount
#
#       ↓
#
# Customer verifies receiver + amount
#
#
# OR
#
#
# OPTION 2:
#
# Customer opens QR section
#
#       ↓
#
# Scans QR
#
#       ↓
#
# Completes payment
#
#
# AFTER PAYMENT:
#
# Customer returns to website
#
#       ↓
#
# Enters UTR / Transaction Reference
#
#       ↓
#
# Payment = Verification Pending
#
#       ↓
#
# Admin manually verifies actual payment
#
#       ├── APPROVE
#       │
#       │      Payment = Paid
#       │      Order processing continues
#       │
#       └── REJECT
#
#              Payment = Rejected
#
#
# IMPORTANT:
#
# UTR submission NEVER automatically means Paid.
#
# Admin verification remains mandatory.
# =========================================================

@login_required(
    login_url="login"
)
def upi_payment(
    request,
    order_id
):


    # =====================================================
    # GET CUSTOMER'S OWN ONLINE ORDER
    #
    # Security:
    #
    # User can only access their own order.
    #
    # Only ONLINE payment orders can access this page.
    # =====================================================

    order = get_object_or_404(

        Order,

        id=order_id,

        user=request.user,

        payment_method="ONLINE",

    )


    # =====================================================
    # GET CURRENT UPI SETTINGS
    # =====================================================

    payment_settings = (

        get_payment_settings()

    )


    # =====================================================
    # CANCELLED ORDER
    #
    # Cancelled orders cannot accept payment.
    # =====================================================

    if order.status == "Cancelled":

        return redirect(

            "order_detail",

            order_id=order.id,

        )


    # =====================================================
    # CREATE / GET PAYMENT
    #
    # One Payment per Order.
    #
    # Payment amount always starts from Order.total_amount.
    # =====================================================

    payment, created = (

        Payment.objects

        .get_or_create(

            order=order,

            defaults={

                "amount":
                    order.total_amount,

                "status":
                    "Pending",

            },

        )

    )


    # =====================================================
    # SYNCHRONIZE EXPECTED PAYMENT AMOUNT
    #
    # Amount ALWAYS comes from Order.
    #
    # Never trust amount submitted by customer.
    #
    # Once payment is Paid, preserve historical amount.
    # =====================================================

    if (

        payment.status
        !=
        "Paid"

        and

        payment.amount
        !=
        order.total_amount

    ):

        payment.amount = (

            order.total_amount

        )


        payment.save(

            update_fields=[

                "amount",

                "updated_at",

            ]

        )


    # =====================================================
    # PAYMENT ALREADY SUBMITTED / VERIFIED
    #
    # Verification Pending:
    #
    # Customer already submitted UTR.
    #
    # Paid:
    #
    # Admin already verified payment.
    #
    # Redirect to payment status page.
    # =====================================================

    if payment.status in [

        "Verification Pending",

        "Paid",

    ]:

        return redirect(

            "payment_status",

            order_id=order.id,

        )


    # =====================================================
    # REJECTED / FAILED PAYMENT
    #
    # Customer can return to this payment page and make
    # another payment attempt.
    #
    # New POST submission replaces the previous UTR.
    #
    # Supported retry statuses:
    #
    # - Rejected
    # - Failed (legacy)
    # =====================================================


    # =====================================================
    # POST - CUSTOMER SUBMITS UTR
    # =====================================================

    if request.method == "POST":


        # =================================================
        # PAYMENT SETTINGS MUST EXIST
        # =================================================

        if payment_settings is None:

            return render(

                request,

                "upi_payment.html",

                payment_page_context(

                    order,

                    payment,

                    payment_settings,

                    (

                        "Online payment is temporarily "
                        "unavailable because payment "
                        "settings have not been configured."

                    ),

                ),

            )


        # =================================================
        # UPI ID MUST EXIST
        #
        # QR code is optional.
        #
        # Main receiving information is UPI ID.
        # =================================================

        if not (

            payment_settings.upi_id

            or ""

        ).strip():

            return render(

                request,

                "upi_payment.html",

                payment_page_context(

                    order,

                    payment,

                    payment_settings,

                    (

                        "Online payment is temporarily "
                        "unavailable because the UPI ID "
                        "has not been configured."

                    ),

                ),

            )


        # =================================================
        # GET UTR FROM FORM
        # =================================================

        transaction_id = (

            normalize_utr(

                request.POST.get(

                    "upi_transaction_id",

                    ""

                )

            )

        )


        # =================================================
        # VALIDATE UTR
        # =================================================

        utr_error = (

            validate_utr(

                transaction_id

            )

        )


        # =================================================
        # RETURN VALIDATION ERROR
        # =================================================

        if utr_error:

            return render(

                request,

                "upi_payment.html",

                payment_page_context(

                    order,

                    payment,

                    payment_settings,

                    utr_error,

                ),

            )


        # =================================================
        # DUPLICATE UTR CHECK
        #
        # Prevent obvious reuse of the same UTR for
        # another order.
        # =================================================

        duplicate_payment = (

            Payment.objects

            .filter(

                upi_transaction_id__iexact=
                    transaction_id

            )

            .exclude(

                id=payment.id

            )

            .exists()

        )


        # =================================================
        # DUPLICATE FOUND
        # =================================================

        if duplicate_payment:

            return render(

                request,

                "upi_payment.html",

                payment_page_context(

                    order,

                    payment,

                    payment_settings,

                    (

                        "This Transaction / UTR number "
                        "has already been submitted for "
                        "another order."

                    ),

                ),

            )


        # =================================================
        # SAVE PAYMENT SUBMISSION SAFELY
        #
        # Use database transaction + row locks.
        # =================================================

        try:

            with transaction.atomic():


                # =========================================
                # LOCK ORDER
                #
                # Prevent concurrent modifications.
                # =========================================

                locked_order = (

                    Order.objects

                    .select_for_update()

                    .get(

                        id=order.id,

                        user=request.user,

                        payment_method="ONLINE",

                    )

                )


                # =========================================
                # LOCK PAYMENT
                # =========================================

                locked_payment = (

                    Payment.objects

                    .select_for_update()

                    .get(

                        id=payment.id,

                        order=locked_order,

                    )

                )


                # =========================================
                # RECHECK CANCELLED ORDER
                # =========================================

                if (

                    locked_order.status
                    ==
                    "Cancelled"

                ):

                    return redirect(

                        "order_detail",

                        order_id=
                            locked_order.id,

                    )


                # =========================================
                # RECHECK PAYMENT STATUS
                #
                # Prevent duplicate submission.
                # =========================================

                if locked_payment.status in [

                    "Verification Pending",

                    "Paid",

                ]:

                    return redirect(

                        "payment_status",

                        order_id=
                            locked_order.id,

                    )


                # =========================================
                # DUPLICATE UTR RECHECK
                #
                # Recheck inside transaction.
                # =========================================

                duplicate_exists = (

                    Payment.objects

                    .filter(

                        upi_transaction_id__iexact=
                            transaction_id

                    )

                    .exclude(

                        id=
                            locked_payment.id

                    )

                    .exists()

                )


                # =========================================
                # DUPLICATE FOUND INSIDE TRANSACTION
                # =========================================

                if duplicate_exists:

                    return render(

                        request,

                        "upi_payment.html",

                        payment_page_context(

                            locked_order,

                            locked_payment,

                            payment_settings,

                            (

                                "This Transaction / UTR "
                                "number has already been "
                                "submitted."

                            ),

                        ),

                    )


                # =========================================
                # SAVE NEW UTR
                #
                # If old payment was Rejected / Failed,
                # this replaces old UTR with the new one.
                # =========================================

                locked_payment.upi_transaction_id = (

                    transaction_id

                )


                # =========================================
                # EXPECTED AMOUNT
                #
                # ALWAYS FROM SERVER-SIDE ORDER.
                #
                # Customer cannot modify this through POST.
                # =========================================

                locked_payment.amount = (

                    locked_order.total_amount

                )


                # =========================================
                # CUSTOMER SUBMITTED TIME
                # =========================================

                locked_payment.submitted_at = (

                    timezone.now()

                )


                # =========================================
                # RESET PREVIOUS VERIFICATION TIME
                #
                # Required for retry after rejection.
                # =========================================

                locked_payment.verified_at = (

                    None

                )


                # =========================================
                # RESET ADMIN NOTE
                #
                # Prevent an old rejection reason from
                # appearing as a current verification note.
                # =========================================

                locked_payment.admin_note = ""


                # =========================================
                # PAYMENT STATUS
                #
                # IMPORTANT:
                #
                # UTR submission DOES NOT mean Paid.
                #
                # Admin must verify actual bank/UPI receipt.
                # =========================================

                locked_payment.status = (

                    "Verification Pending"

                )


                # =========================================
                # SAVE PAYMENT
                # =========================================

                locked_payment.save(

                    update_fields=[

                        "upi_transaction_id",

                        "amount",

                        "submitted_at",

                        "verified_at",

                        "admin_note",

                        "status",

                        "updated_at",

                    ]

                )


                # =========================================
                # ORDER PAYMENT STATUS
                #
                # Still Pending until admin approves.
                # =========================================

                locked_order.payment_status = (

                    "Pending"

                )


                # =========================================
                # IMPORTANT
                #
                # DO NOT CONFIRM ORDER HERE.
                #
                # Customer has only submitted a UTR.
                #
                # Admin verification must happen first.
                #
                # Order processing should start only after
                # verified payment.
                # =========================================

                locked_order.save(

                    update_fields=[

                        "payment_status",

                        "updated_at",

                    ]

                )


                # =========================================
                # UPDATE LOCAL REFERENCES
                # =========================================

                order = (

                    locked_order

                )


                payment = (

                    locked_payment

                )


        # =================================================
        # DATABASE INTEGRITY ERROR
        #
        # Handles possible duplicate UTR / DB constraint
        # problems safely.
        # =================================================

        except IntegrityError:

            return render(

                request,

                "upi_payment.html",

                payment_page_context(

                    order,

                    payment,

                    payment_settings,

                    (

                        "This Transaction / UTR number "
                        "has already been submitted. "
                        "Please check the number and "
                        "try again."

                    ),

                ),

            )


        # =================================================
        # OTHER ERROR
        # =================================================

        except Exception as error:

            print(

                "PAYMENT SUBMISSION ERROR:",

                repr(
                    error
                )

            )


            return render(

                request,

                "upi_payment.html",

                payment_page_context(

                    order,

                    payment,

                    payment_settings,

                    (

                        "Unable to submit your payment "
                        "details right now. "
                        "Please try again."

                    ),

                ),

            )


        # =================================================
        # CLEAR CART
        #
        # Order already exists.
        #
        # Customer successfully submitted their payment
        # reference for admin verification.
        # =================================================

        request.session["cart"] = {}


        request.session.modified = (

            True

        )


        # =================================================
        # REDIRECT TO PAYMENT STATUS
        # =================================================

        return redirect(

            "payment_status",

            order_id=order.id,

        )


    # =====================================================
    # GET - DISPLAY PAYMENT PAGE
    # =====================================================

    return render(

        request,

        "upi_payment.html",

        payment_page_context(

            order,

            payment,

            payment_settings,

        ),

    )


# =========================================================
# PAYMENT STATUS PAGE
#
# Customer can see:
#
# - Pending
# - Verification Pending
# - Paid
# - Rejected
# - Failed (legacy)
# =========================================================

@login_required(
    login_url="login"
)
def payment_status(
    request,
    order_id
):


    # =====================================================
    # GET CUSTOMER'S OWN ONLINE ORDER
    # =====================================================

    order = get_object_or_404(

        Order,

        id=order_id,

        user=request.user,

        payment_method="ONLINE",

    )


    # =====================================================
    # GET PAYMENT
    # =====================================================

    payment = get_object_or_404(

        Payment,

        order=order,

    )


    # =====================================================
    # GET CURRENT PAYMENT SETTINGS
    # =====================================================

    payment_settings = (

        get_payment_settings()

    )


    # =====================================================
    # GET ORDER ITEMS
    # =====================================================

    order_items = (

        order.items

        .select_related(

            "product",

            "customization",

        )

        .all()

    )


    # =====================================================
    # RENDER PAYMENT STATUS PAGE
    # =====================================================

    return render(

        request,

        "payments_status.html",

        {

            "order":
                order,

            "payment":
                payment,

            "payment_settings":
                payment_settings,

            "order_items":
                order_items,

        },

    )