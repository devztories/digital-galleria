from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


# =========================================================
# ADVERTISEMENT MODEL
#
# Supports:
#
# 1. TEXT ADVERTISEMENT
#    - Scrolling text on homepage
#    - Right → Left
#
# 2. IMAGE ADVERTISEMENT
#    - Popup advertisement
#    - Once per browser session
#    - Close button handled in home.html
#
# Ads appear only when:
#
# - is_active = True
# - start_at is empty OR start_at <= now
# - end_at is empty OR end_at >= now
# =========================================================

class Advertisement(models.Model):

    # =====================================================
    # ADVERTISEMENT TYPES
    # =====================================================

    TEXT = "text"
    IMAGE = "image"

    AD_TYPE_CHOICES = [

        (
            TEXT,
            "Text Advertisement"
        ),

        (
            IMAGE,
            "Image Advertisement"
        ),

    ]


    # =====================================================
    # TITLE
    # =====================================================

    title = models.CharField(

        max_length=200,

        blank=True,

        default="",

        help_text=(
            "Internal title used to identify "
            "this advertisement."
        ),

    )


    # =====================================================
    # ADVERTISEMENT TYPE
    # =====================================================

    ad_type = models.CharField(

        max_length=10,

        choices=AD_TYPE_CHOICES,

        default=TEXT,

        db_index=True,

        help_text=(

            "Choose Text Advertisement "
            "or Image Advertisement."

        ),

    )


    # =====================================================
    # TEXT ADVERTISEMENT
    # =====================================================

    text = models.TextField(

        blank=True,

        default="",

        help_text=(

            "Required only for Text Advertisement. "
            "This text will scroll from right to left "
            "on the homepage."

        ),

    )


    # =====================================================
    # IMAGE ADVERTISEMENT
    # =====================================================

    image = models.ImageField(

        upload_to="advertisements/",

        blank=True,

        null=True,

        help_text=(

            "Required only for Image Advertisement."

        ),

    )


    # =====================================================
    # OPTIONAL LINK
    # =====================================================

    link = models.URLField(

        blank=True,

        default="",

        help_text=(

            "Optional link opened when the "
            "advertisement is clicked."

        ),

    )


    # =====================================================
    # ACTIVE / INACTIVE
    # =====================================================

    is_active = models.BooleanField(

        default=True,

        db_index=True,

        help_text=(

            "Turn this ON to allow the "
            "advertisement to appear."

        ),

    )


    # =====================================================
    # START DATE / TIME
    # =====================================================

    start_at = models.DateTimeField(

        blank=True,

        null=True,

        db_index=True,

        help_text=(

            "Optional. Leave blank to start immediately."

        ),

    )


    # =====================================================
    # END DATE / TIME
    # =====================================================

    end_at = models.DateTimeField(

        blank=True,

        null=True,

        db_index=True,

        help_text=(

            "Optional. Leave blank if the advertisement "
            "should remain active until manually disabled."

        ),

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
        # TEXT AD VALIDATION
        # -------------------------------------------------

        if self.ad_type == self.TEXT:

            if not self.text.strip():

                raise ValidationError(

                    {

                        "text":

                            "Please enter advertisement text "
                            "for a Text Advertisement."

                    }

                )


        # -------------------------------------------------
        # IMAGE AD VALIDATION
        # -------------------------------------------------

        if self.ad_type == self.IMAGE:

            if not self.image:

                raise ValidationError(

                    {

                        "image":

                            "Please upload an image "
                            "for an Image Advertisement."

                    }

                )


        # -------------------------------------------------
        # DATE VALIDATION
        # -------------------------------------------------

        if (

            self.start_at

            and

            self.end_at

            and

            self.end_at <= self.start_at

        ):

            raise ValidationError(

                {

                    "end_at":

                        "End date/time must be after "
                        "the start date/time."

                }

            )


    # =====================================================
    # CURRENTLY ACTIVE
    # =====================================================

    @property
    def currently_active(self):

        if not self.is_active:

            return False


        now = timezone.now()


        if (

            self.start_at

            and

            now < self.start_at

        ):

            return False


        if (

            self.end_at

            and

            now > self.end_at

        ):

            return False


        if (

            self.ad_type == self.TEXT

            and

            not self.text.strip()

        ):

            return False


        if (

            self.ad_type == self.IMAGE

            and

            not self.image

        ):

            return False


        return True


    # =====================================================
    # DISPLAY NAME IN ADMIN
    # =====================================================

    def __str__(self):

        if self.title:

            return self.title


        if self.ad_type == self.TEXT:

            return (

                f"Text Advertisement #{self.pk}"

            )


        return (

            f"Image Advertisement #{self.pk}"

        )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = [

            "-created_at",

        ]

        verbose_name = (

            "Advertisement"

        )

        verbose_name_plural = (

            "Advertisements"

        )


# =========================================================
# SOCIAL MEDIA LINKS
# =========================================================

class SocialMediaLink(models.Model):

    PLATFORM_CHOICES = [

        (
            "instagram",
            "Instagram"
        ),

        (
            "facebook",
            "Facebook"
        ),

        (
            "youtube",
            "YouTube"
        ),

        (
            "whatsapp",
            "WhatsApp"
        ),

    ]


    platform = models.CharField(

        max_length=20,

        choices=PLATFORM_CHOICES,

        unique=True,

    )


    url = models.URLField(

        help_text=(

            "Enter the full social media profile URL."

        )

    )


    is_active = models.BooleanField(

        default=True

    )


    def __str__(self):

        return (

            self.get_platform_display()

        )


# =========================================================
# ABOUT SECTION
# =========================================================

class AboutSection(models.Model):


    title = models.CharField(

        max_length=200,

        default="About Digital Galleria"

    )


    image = models.ImageField(

        upload_to="about/",

        blank=True,

        null=True,

    )


    name = models.CharField(

        max_length=200,

        blank=True,

    )


    subtitle = models.CharField(

        max_length=200,

        blank=True,

    )


    description = models.TextField(

        blank=True,

    )


    email = models.EmailField(

        blank=True,

    )


    phone = models.CharField(

        max_length=30,

        blank=True,

    )


    is_active = models.BooleanField(

        default=True

    )


    updated_at = models.DateTimeField(

        auto_now=True

    )


    def __str__(self):

        return self.title


# =========================================================
# CUSTOMIZATION SETTINGS
#
# Controls how customers can send customization photos.
#
# Admin can configure:
#
# - WhatsApp direct chat link
# - Enable / disable WhatsApp photo submission
# - Optional customer instructions
#
#
# IMPORTANT:
#
# We store a DIRECT WHATSAPP CHAT LINK.
#
# No WhatsApp phone number needs to be hard-coded
# anywhere in the website code.
#
#
# Example links:
#
# https://wa.me/91XXXXXXXXXX
#
# or any valid WhatsApp direct-chat URL.
#
#
# CUSTOMER FLOW:
#
# Customize Product
#       ↓
# Choose:
#
# 1. Upload Photos Here
#
# OR
#
# 2. Send Photos via WhatsApp
#       ↓
# Open WhatsApp
#       ↓
# Customer sends photos manually
#       ↓
# Returns to website
#       ↓
# Checks:
#
# ☑ I have sent my photos via WhatsApp
#       ↓
# Add Customized Product to Cart
#
# =========================================================

class CustomizationSettings(models.Model):


    # =====================================================
    # WHATSAPP SUBMISSION ENABLED
    #
    # Admin can temporarily disable WhatsApp photo
    # submission without changing code.
    #
    # False:
    #
    # Customer will only see normal website upload.
    #
    # =====================================================

    whatsapp_enabled = models.BooleanField(

        default=True,

        help_text=(

            "Enable this to allow customers to send "
            "customization photos through WhatsApp."

        ),

    )


    # =====================================================
    # WHATSAPP DIRECT CHAT LINK
    #
    # IMPORTANT:
    #
    # Paste the complete WhatsApp direct chat link.
    #
    # No phone number is hard-coded in the website.
    #
    # =====================================================

    whatsapp_chat_link = models.URLField(

        max_length=500,

        blank=True,

        default="",

        help_text=(

            "Paste the full WhatsApp direct chat link. "
            "Customers will be sent directly to this chat."

        ),

    )


    # =====================================================
    # WHATSAPP OPTION TITLE
    #
    # Customer-facing title.
    #
    # =====================================================

    whatsapp_title = models.CharField(

        max_length=150,

        default="Send Photos via WhatsApp",

        blank=True,

    )


    # =====================================================
    # WHATSAPP CUSTOMER INSTRUCTIONS
    #
    # Displayed before customer opens WhatsApp.
    #
    # =====================================================

    whatsapp_instructions = models.TextField(

        blank=True,

        default=(

            "Send all customization photos through "
            "WhatsApp. After sending the photos, return "
            "to this page and confirm that you have "
            "sent them."

        ),

    )


    # =====================================================
    # WEBSITE UPLOAD TITLE
    # =====================================================

    website_upload_title = models.CharField(

        max_length=150,

        default="Upload Photos Here",

        blank=True,

    )


    # =====================================================
    # WEBSITE UPLOAD DESCRIPTION
    # =====================================================

    website_upload_description = models.TextField(

        blank=True,

        default=(

            "Upload your customization photos directly "
            "from your device."

        ),

    )


    # =====================================================
    # UPDATED TIME
    # =====================================================

    updated_at = models.DateTimeField(

        auto_now=True

    )


    # =====================================================
    # VALIDATION
    # =====================================================

    def clean(self):

        super().clean()


        # If WhatsApp is enabled,
        # a chat link must be provided.

        if (

            self.whatsapp_enabled

            and

            not self.whatsapp_chat_link.strip()

        ):

            raise ValidationError(

                {

                    "whatsapp_chat_link":

                        "Please enter a WhatsApp direct "
                        "chat link when WhatsApp photo "
                        "submission is enabled."

                }

            )


    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return (

            "Customization Settings"

        )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        verbose_name = (

            "Customization Setting"

        )

        verbose_name_plural = (

            "Customization Settings"

        )