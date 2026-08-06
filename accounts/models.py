from django.db import models
<<<<<<< HEAD
from django.contrib.auth.models import User


class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    pincode = models.CharField(
        max_length=10,
        blank=True
    )
=======
from django.contrib.auth.models import AbstractUser


# =========================================================
# CUSTOM USER MODEL
# =========================================================

class User(AbstractUser):

    # =====================================================
    # PHONE NUMBER
    # =====================================================

    phone = models.CharField(
        max_length=15,
        blank=True,
    )


    # =====================================================
    # PROFILE IMAGE
    # =====================================================
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
<<<<<<< HEAD
        null=True
    )

    def __str__(self):
        return self.user.username
=======
        null=True,
    )


    # =====================================================
    # CREATED DATE
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    # =====================================================
    # DISPLAY
    # =====================================================

    def __str__(self):

        return self.username


# =========================================================
# SAVED ADDRESS MODEL
#
# One user can have multiple addresses:
#
# Home
# Office
# Other
#
# Only one address will be default.
# =========================================================

class Address(models.Model):

    # =====================================================
    # ADDRESS TYPES
    # =====================================================

    ADDRESS_TYPE_CHOICES = [

        (
            "home",
            "Home",
        ),

        (
            "office",
            "Office",
        ),

        (
            "other",
            "Other",
        ),

    ]


    # =====================================================
    # USER
    # =====================================================

    user = models.ForeignKey(

        User,

        on_delete=models.CASCADE,

        related_name="addresses",

    )


    # =====================================================
    # ADDRESS TYPE
    # =====================================================

    address_type = models.CharField(

        max_length=20,

        choices=ADDRESS_TYPE_CHOICES,

        default="home",

    )


    # =====================================================
    # RECEIVER NAME
    # =====================================================

    full_name = models.CharField(

        max_length=150,

    )


    # =====================================================
    # PHONE
    # =====================================================

    phone = models.CharField(

        max_length=15,

    )


    # =====================================================
    # ADDRESS LINE 1
    #
    # House / Flat / Building / Street
    # =====================================================

    address_line1 = models.CharField(

        max_length=255,

    )


    # =====================================================
    # ADDRESS LINE 2
    #
    # Area / Landmark / Locality
    # =====================================================

    address_line2 = models.CharField(

        max_length=255,

        blank=True,

    )


    # =====================================================
    # CITY
    # =====================================================

    city = models.CharField(

        max_length=100,

    )


    # =====================================================
    # STATE
    # =====================================================

    state = models.CharField(

        max_length=100,

    )


    # =====================================================
    # PINCODE
    # =====================================================

    pincode = models.CharField(

        max_length=10,

    )


    # =====================================================
    # DEFAULT ADDRESS
    # =====================================================

    is_default = models.BooleanField(

        default=False,

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
    # META
    # =====================================================

    class Meta:

        ordering = [

            "-is_default",

            "-updated_at",

        ]

        verbose_name = (
            "Saved Address"
        )

        verbose_name_plural = (
            "Saved Addresses"
        )


    # =====================================================
    # SAVE
    #
    # Rules:
    #
    # 1. First address automatically becomes default.
    #
    # 2. If one address becomes default,
    #    all other addresses become non-default.
    # =====================================================

    def save(
        self,
        *args,
        **kwargs
    ):

        # -------------------------------------------------
        # FIRST ADDRESS
        # -------------------------------------------------

        if not self.pk:

            user_has_address = (

                Address.objects

                .filter(
                    user=self.user
                )

                .exists()

            )


            if not user_has_address:

                self.is_default = True


        # -------------------------------------------------
        # SAVE CURRENT ADDRESS
        # -------------------------------------------------

        super().save(
            *args,
            **kwargs
        )


        # -------------------------------------------------
        # REMOVE DEFAULT FROM OTHER ADDRESSES
        # -------------------------------------------------

        if self.is_default:

            Address.objects.filter(

                user=self.user,

            ).exclude(

                pk=self.pk,

            ).update(

                is_default=False

            )


    # =====================================================
    # FULL ADDRESS
    # =====================================================

    @property
    def full_address(self):

        parts = [

            self.address_line1,

            self.address_line2,

            self.city,

            self.state,

            self.pincode,

        ]


        return ", ".join(

            str(part).strip()

            for part in parts

            if part

        )


    # =====================================================
    # DISPLAY
    # =====================================================

    def __str__(self):

        default_text = (

            " - Default"

            if self.is_default

            else ""

        )


        return (

            f"{self.full_name} - "

            f"{self.get_address_type_display()}"

            f"{default_text}"

        )
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321
