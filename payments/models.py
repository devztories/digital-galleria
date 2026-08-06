from django.db import models
from orders.models import Order


# =========================================================
# PAYMENT
#
# FINAL PAYMENT FLOW
#
# Customer places order
#       ↓
# Payment page opens
#       ↓
# Customer sees exact amount to pay
#       ↓
# Customer chooses:
#
#   1. Open UPI App
#
#      Website sends:
#
#      - UPI ID
#      - UPI Receiver Name
#      - Exact Order Amount
#      - Currency = INR
#      - Order Reference
#
#      Supported UPI apps should automatically
#      pre-fill the exact order amount.
#
#      If a particular UPI app/device does not
#      pre-fill the amount, customer can manually
#      enter the exact amount shown on the website.
#
#   OR
#
#   2. Pay Using QR Code
#
#      - Customer opens QR section
#      - Scans QR
#      - Pays exact displayed amount
#
#       ↓
# Customer completes payment
#       ↓
# Enters UTR / Transaction ID
#       ↓
# Payment = Verification Pending
#       ↓
# Admin verifies later
#
#       ├── APPROVE
#       │      ↓
#       │   Payment = Paid
#       │   Order processing continues
#       │
#       └── REJECT
#              ↓
#           Payment = Rejected
#
#
# IMPORTANT:
#
# Submitting a UTR does NOT mean payment is verified.
#
# Only admin verification should mark payment as Paid.
# =========================================================


class Payment(models.Model):


    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    STATUS_CHOICES = [

        (
            "Pending",
            "Pending"
        ),

        (
            "Verification Pending",
            "Verification Pending"
        ),

        (
            "Paid",
            "Paid"
        ),

        (
            "Rejected",
            "Rejected"
        ),

        # -------------------------------------------------
        # LEGACY STATUS
        #
        # Keep this so existing database records/code
        # using "Failed" do not immediately break.
        # -------------------------------------------------

        (
            "Failed",
            "Failed"
        ),

    ]


    # =====================================================
    # ORDER
    #
    # One order has one Payment record.
    # =====================================================

    order = models.OneToOneField(
    "orders.Order",
    on_delete=models.CASCADE,
    related_name="payment"
)


    # =====================================================
    # UPI TRANSACTION ID / UTR
    #
    # Customer enters this AFTER making payment.
    #
    # IMPORTANT:
    #
    # UTR submission does NOT automatically mean
    # the payment is successful.
    #
    # Admin must verify the actual payment.
    # =====================================================

    upi_transaction_id = models.CharField(

        max_length=100,

        blank=True,

        null=True,

        db_index=True,

        verbose_name="UPI Transaction ID / UTR"

    )


    # =====================================================
    # EXPECTED PAYMENT AMOUNT
    #
    # IMPORTANT:
    #
    # This value must always come from:
    #
    #       Order.total_amount
    #
    # Never trust:
    #
    # - Customer input
    # - POST amount
    # - GET amount
    # - JavaScript amount
    #
    # The server-side Order.total_amount is the
    # authoritative amount.
    # =====================================================

    amount = models.DecimalField(

        max_digits=10,

        decimal_places=2

    )


    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    status = models.CharField(

        max_length=30,

        choices=STATUS_CHOICES,

        default="Pending",

        db_index=True

    )


    # =====================================================
    # STOCK PROCESSED
    #
    # Prevents stock operations from running twice.
    #
    # Example:
    #
    # Admin accidentally approves the same payment twice.
    #
    # Stock deduction logic should check this flag before
    # changing product stock.
    # =====================================================

    stock_processed = models.BooleanField(

        default=False

    )


    # =====================================================
    # CUSTOMER SUBMITTED TIME
    #
    # Set when customer submits UTR.
    # =====================================================

    submitted_at = models.DateTimeField(

        blank=True,

        null=True

    )


    # =====================================================
    # VERIFIED TIME
    #
    # Set when admin successfully verifies payment.
    # =====================================================

    verified_at = models.DateTimeField(

        blank=True,

        null=True

    )


    # =====================================================
    # ADMIN NOTE
    #
    # Examples:
    #
    # "UTR verified in bank statement."
    #
    # "Transaction not found."
    #
    # "Amount received was incorrect."
    # =====================================================

    admin_note = models.TextField(

        blank=True,

        default=""

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

            f"Payment - "
            f"Order #{self.order_id} - "
            f"{self.status}"

        )


# =========================================================
# UPI PAYMENT SETTINGS
#
# Admin controls UPI receiving details.
#
#
# IMPORTANT:
#
# This configuration supports a PERSONAL UPI ID.
#
#
# Example:
#
# UPI Receiver Name:
#
#       Devadathan R
#
# UPI ID:
#
#       example@oksbi
#
#
# CUSTOMER PAYMENT FLOW:
#
#       Exact Amount To Pay
#
#           ₹500.00
#
#       UPI Receiver Name
#
#           Devadathan R
#
#       UPI ID
#
#           example@oksbi
#
#       [ Copy UPI ID ]
#
#       [ Open UPI App ]
#
#               ↓
#
# UPI deep link sends:
#
#       pa = UPI ID
#       pn = Receiver Name
#       am = Exact Order Amount
#       cu = INR
#       tn = Order Reference
#
#               ↓
#
# Supported UPI app should pre-fill:
#
#       Receiver
#       +
#       ₹500.00
#
#
# FALLBACK:
#
# If the selected UPI app does not automatically
# pre-fill the amount, customer manually enters the
# exact amount displayed on the website.
#
#
# QR OPTION:
#
#       ☐ Pay Using QR Code
#
#               ↓
#
#           QR CODE
#
#
# AFTER PAYMENT:
#
#       Customer enters UTR
#
#               ↓
#
#       Verification Pending
#
#               ↓
#
#       Admin verifies
#
#
# PaymentSettings itself does NOT verify payments.
# =========================================================


class PaymentSettings(models.Model):


    # =====================================================
    # UPI RECEIVER NAME
    #
    # Enter the receiver/payee name corresponding to
    # the configured UPI ID.
    #
# Example:
    #
    #       Devadathan R
    #
    # IMPORTANT:
    #
    # Do NOT automatically use "Digital Galleria"
    # unless that is actually the appropriate receiver
    # name for the configured UPI ID.
    #
    # For a personal UPI ID, enter the corresponding
    # receiver/payee name.
    # =====================================================

    upi_receiver_name = models.CharField(

        max_length=150,

        default="",

        blank=True,

        verbose_name="UPI Receiver Name",

        help_text=(

            "Enter the receiver/payee name associated "
            "with the configured UPI ID."

        )

    )


    # =====================================================
    # UPI ID
    #
    # Examples:
    #
    #       example@oksbi
    #
    #       example@okaxis
    #
    #       example@ybl
    #
    #
    # Customer can:
    #
    # - Copy this UPI ID
    #
    # - Open a supported UPI application
    #
    #
    # The payment view generates a UPI deep link with:
    #
    # - UPI ID
    # - Receiver Name
    # - Exact Order Amount
    # - INR
    # - Order Reference
    #
    #
    # IMPORTANT:
    #
    # Exact amount comes from Order.total_amount.
    # =====================================================

    upi_id = models.CharField(

        max_length=100,

        blank=True,

        verbose_name="UPI ID",

        help_text=(

            "Enter the UPI ID that should receive "
            "customer payments."

        )

    )


    # =====================================================
    # QR CODE
    #
    # Admin uploads the receiving QR code.
    #
    # This is an optional alternative payment method.
    #
    #
    # Customer page:
    #
    #       ☐ Pay Using QR Code
    #
    #               ↓
    #
    # QR becomes visible.
    #
    #
    # Customer scans the QR using their UPI app and
    # verifies the receiver and amount before paying.
    # =====================================================

    qr_code = models.ImageField(

        upload_to="payment_qr/",

        blank=True,

        null=True,

        verbose_name="UPI QR Code",

        help_text=(

            "Optional. Upload the QR code used to "
            "receive UPI payments."

        )

    )


    # =====================================================
    # PAYMENT INSTRUCTIONS
    #
    # Admin can customize these instructions.
    #
    # IMPORTANT:
    #
    # Automatic amount pre-fill depends on whether the
    # selected UPI app/device supports the deep-link
    # parameters correctly.
    #
    # Therefore a manual amount fallback is mentioned.
    # =====================================================

    instructions = models.TextField(

        blank=True,

        default=(

            "Tap Open UPI App and verify the receiver "
            "details and exact payment amount before paying. "
            "The exact order amount should be automatically "
            "passed to supported UPI apps. "
            "If your UPI app does not automatically show "
            "the amount, manually enter the exact amount "
            "displayed on this payment page. "
            "After completing the payment, return to this "
            "page and enter the UTR / Transaction Reference "
            "Number for verification."

        ),

        verbose_name="Payment Instructions"

    )


    # =====================================================
    # UPDATED TIME
    # =====================================================

    updated_at = models.DateTimeField(

        auto_now=True

    )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        verbose_name = (

            "UPI Payment Setting"

        )

        verbose_name_plural = (

            "UPI Payment Settings"

        )


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        receiver_name = (

            self.upi_receiver_name

            or

            "Receiver Not Configured"

        )

        return (

            f"UPI Settings - "
            f"{receiver_name}"

        )