from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# =========================================================
# COUPON
#
# Admin can create promotional coupon codes.
#
# Example:
#
# Code: JUNE20
# Discount: 20%
# Valid From: June 1
# Valid Until: June 30
# Active: Yes
#
# Customer enters JUNE20 during checkout.
# =========================================================

class Coupon(models.Model):

    # =====================================================
    # COUPON CODE
    #
    # Example:
    #
    # JUNE20
    # ONAM30
    # NEWYEAR10
    #
    # unique=True prevents duplicate coupon codes.
    # =====================================================

    code = models.CharField(
        max_length=50,
        unique=True,
    )


    # =====================================================
    # DISCOUNT PERCENTAGE
    #
    # Example:
    #
    # 20 = 20% discount
    # 30 = 30% discount
    # =====================================================

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )


    # =====================================================
    # VALID FROM
    # =====================================================

    valid_from = models.DateTimeField()


    # =====================================================
    # VALID UNTIL
    # =====================================================

    valid_until = models.DateTimeField()


    # =====================================================
    # ACTIVE
    #
    # Admin can manually disable a coupon at any time.
    # =====================================================

    is_active = models.BooleanField(
        default=True,
    )


    # =====================================================
    # OPTIONAL MINIMUM ORDER AMOUNT
    #
    # Example:
    #
    # ₹0
    #     Coupon works for any order.
    #
    # ₹1000
    #     Coupon only works when subtotal >= ₹1000.
    # =====================================================

    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )


    # =====================================================
    # CREATED / UPDATED
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    # =====================================================
    # MODEL VALIDATION
    # =====================================================

    def clean(self):

        super().clean()


        # -------------------------------------------------
        # CODE
        # -------------------------------------------------

        if self.code:

            self.code = (
                self.code
                .strip()
                .upper()
            )


        # -------------------------------------------------
        # DISCOUNT MUST BE BETWEEN 0 AND 100
        # -------------------------------------------------

        if self.discount_percentage is not None:

            if (
                self.discount_percentage <= 0
                or
                self.discount_percentage > 100
            ):

                raise ValidationError(
                    {
                        "discount_percentage":
                            (
                                "Discount percentage must "
                                "be greater than 0 and "
                                "not more than 100."
                            )
                    }
                )


        # -------------------------------------------------
        # VALIDITY CHECK
        # -------------------------------------------------

        if (
            self.valid_from
            and
            self.valid_until
            and
            self.valid_until <= self.valid_from
        ):

            raise ValidationError(
                {
                    "valid_until":
                        (
                            "Valid Until must be later "
                            "than Valid From."
                        )
                }
            )


        # -------------------------------------------------
        # MINIMUM AMOUNT CANNOT BE NEGATIVE
        # -------------------------------------------------

        if (
            self.minimum_order_amount is not None
            and
            self.minimum_order_amount < 0
        ):

            raise ValidationError(
                {
                    "minimum_order_amount":
                        (
                            "Minimum order amount "
                            "cannot be negative."
                        )
                }
            )


    # =====================================================
    # SAVE
    #
    # Always save coupon codes in uppercase.
    #
    # june20 -> JUNE20
    # =====================================================

    def save(
        self,
        *args,
        **kwargs
    ):

        if self.code:

            self.code = (
                self.code
                .strip()
                .upper()
            )

        self.full_clean()

        super().save(
            *args,
            **kwargs
        )


    # =====================================================
    # CHECK WHETHER COUPON IS CURRENTLY VALID
    # =====================================================

    @property
    def is_currently_valid(self):

        now = timezone.now()

        return (

            self.is_active

            and

            self.valid_from
            <=
            now

            <=

            self.valid_until

        )


    # =====================================================
    # CALCULATE DISCOUNT
    #
    # Example:
    #
    # subtotal = ₹2000
    # discount = 20%
    #
    # discount amount = ₹400
    # =====================================================

    def calculate_discount(
        self,
        subtotal
    ):

        subtotal = Decimal(
            str(subtotal)
        )


        percentage = Decimal(
            str(
                self.discount_percentage
            )
        )


        discount = (

            subtotal

            *

            percentage

            /

            Decimal("100")

        )


        return discount.quantize(
            Decimal("0.01")
        )


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return (
            f"{self.code} - "
            f"{self.discount_percentage}% OFF"
        )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = [
            "-created_at",
        ]

        verbose_name = "Coupon"

        verbose_name_plural = "Coupons"