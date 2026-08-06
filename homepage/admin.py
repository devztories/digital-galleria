from django.contrib import admin

from .models import (
    Advertisement,
    SocialMediaLink,
    AboutSection,
    CustomizationSettings,
)


# =========================================================
# ADVERTISEMENT ADMIN
# =========================================================

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):

    # =====================================================
    # LIST PAGE
    # =====================================================

    list_display = (

        "title",

        "ad_type",

        "is_active",

        "start_at",

        "end_at",

        "created_at",

    )


    # =====================================================
    # FILTERS
    # =====================================================

    list_filter = (

        "ad_type",

        "is_active",

    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_fields = (

        "title",

        "text",

    )


    # =====================================================
    # ORDERING
    # =====================================================

    ordering = (

        "-created_at",

    )


    # =====================================================
    # ADMIN FORM SECTIONS
    # =====================================================

    fieldsets = (

        # -------------------------------------------------
        # BASIC DETAILS
        # -------------------------------------------------

        (
            "Advertisement Type",

            {

                "fields": (

                    "title",

                    "ad_type",

                    "is_active",

                ),

            },

        ),


        # -------------------------------------------------
        # TEXT ADVERTISEMENT
        # -------------------------------------------------

        (
            "Text Advertisement",

            {

                "fields": (

                    "text",

                ),

                "description": (

                    "Use this field when Advertisement Type "
                    "is Text Advertisement. "
                    "The text will scroll from right to left "
                    "on the homepage."

                ),

            },

        ),


        # -------------------------------------------------
        # IMAGE ADVERTISEMENT
        # -------------------------------------------------

        (
            "Image Advertisement",

            {

                "fields": (

                    "image",

                ),

                "description": (

                    "Use this field when Advertisement Type "
                    "is Image Advertisement. "
                    "The image will appear as a popup "
                    "on the homepage."

                ),

            },

        ),


        # -------------------------------------------------
        # OPTIONAL LINK
        # -------------------------------------------------

        (
            "Advertisement Link",

            {

                "fields": (

                    "link",

                ),

                "description": (

                    "Optional. Add a URL if clicking "
                    "the advertisement should open "
                    "another page."

                ),

            },

        ),


        # -------------------------------------------------
        # SCHEDULE
        # -------------------------------------------------

        (
            "Schedule",

            {

                "fields": (

                    "start_at",

                    "end_at",

                ),

                "description": (

                    "Optional. Set the advertisement "
                    "start and expiry date/time. "
                    "Leave blank if no schedule is required."

                ),

            },

        ),

    )


# =========================================================
# SOCIAL MEDIA LINK ADMIN
#
# Admin can manage:
#
# - Instagram
# - Facebook
# - YouTube
# - WhatsApp
#
# Only active links will be displayed on homepage.
# =========================================================

@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):

    # =====================================================
    # LIST PAGE
    # =====================================================

    list_display = (

        "platform",

        "url",

        "is_active",

    )


    # =====================================================
    # FILTERS
    # =====================================================

    list_filter = (

        "is_active",

        "platform",

    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_fields = (

        "platform",

        "url",

    )


    # =====================================================
    # ADMIN FORM
    # =====================================================

    fieldsets = (

        (
            "Social Media Details",

            {

                "fields": (

                    "platform",

                    "url",

                    "is_active",

                ),

                "description": (

                    "Select the social media platform, "
                    "enter the official profile URL, "
                    "and enable it to display on the homepage."

                ),

            },

        ),

    )


# =========================================================
# ABOUT SECTION ADMIN
#
# Controls the homepage About section.
#
# Admin can manage:
#
# - Title
# - Image / Logo
# - Name
# - Subtitle
# - Description
# - Email
# - Phone
# - Active status
# =========================================================

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):

    # =====================================================
    # LIST PAGE
    # =====================================================

    list_display = (

        "title",

        "name",

        "is_active",

        "updated_at",

    )


    # =====================================================
    # FILTER
    # =====================================================

    list_filter = (

        "is_active",

    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_fields = (

        "title",

        "name",

        "subtitle",

        "description",

        "email",

        "phone",

    )


    # =====================================================
    # ORDERING
    # =====================================================

    ordering = (

        "-updated_at",

    )


    # =====================================================
    # ADMIN FORM SECTIONS
    # =====================================================

    fieldsets = (

        # -------------------------------------------------
        # BASIC INFORMATION
        # -------------------------------------------------

        (
            "About Section",

            {

                "fields": (

                    "title",

                    "is_active",

                ),

            },

        ),


        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        (
            "Image / Logo",

            {

                "fields": (

                    "image",

                ),

                "description": (

                    "Upload the image or logo that should "
                    "appear in the About section."

                ),

            },

        ),


        # -------------------------------------------------
        # PERSON / COMPANY INFORMATION
        # -------------------------------------------------

        (
            "Details",

            {

                "fields": (

                    "name",

                    "subtitle",

                    "description",

                ),

                "description": (

                    "These details can be displayed when "
                    "the customer clicks the About image."

                ),

            },

        ),


        # -------------------------------------------------
        # CONTACT INFORMATION
        # -------------------------------------------------

        (
            "Contact Information",

            {

                "fields": (

                    "email",

                    "phone",

                ),

            },

        ),

    )


# =========================================================
# CUSTOMIZATION SETTINGS ADMIN
#
# Controls the photo submission methods shown on the
# product customization page.
#
#
# CUSTOMER CAN CHOOSE:
#
# 1. Upload Photos Here
#
# OR
#
# 2. Send Photos via WhatsApp
#
#
# Admin can:
#
# - Enable / disable WhatsApp photo submission
#
# - Paste/change WhatsApp direct chat link
#
# - Change WhatsApp option title
#
# - Change WhatsApp customer instructions
#
# - Change website upload title/description
#
#
# IMPORTANT:
#
# No WhatsApp phone number is hard-coded.
#
# Admin only needs to paste the direct WhatsApp chat URL.
#
# =========================================================

@admin.register(CustomizationSettings)
class CustomizationSettingsAdmin(admin.ModelAdmin):


    # =====================================================
    # LIST PAGE
    # =====================================================

    list_display = (

        "settings_name",

        "whatsapp_enabled",

        "whatsapp_link_configured",

        "updated_at",

    )


    # =====================================================
    # READ ONLY
    # =====================================================

    readonly_fields = (

        "updated_at",

    )


    # =====================================================
    # ADMIN FORM SECTIONS
    # =====================================================

    fieldsets = (


        # -------------------------------------------------
        # WHATSAPP SETTINGS
        # -------------------------------------------------

        (
            "WhatsApp Photo Submission",

            {

                "fields": (

                    "whatsapp_enabled",

                    "whatsapp_chat_link",

                    "whatsapp_title",

                    "whatsapp_instructions",

                ),

                "description": (

                    "Enable WhatsApp photo submission and "
                    "paste the full direct WhatsApp chat link. "
                    "Customers who choose this option will "
                    "open this link, send their customization "
                    "photos manually through WhatsApp, return "
                    "to the website, and confirm that the "
                    "photos were sent."

                ),

            },

        ),


        # -------------------------------------------------
        # WEBSITE UPLOAD SETTINGS
        # -------------------------------------------------

        (
            "Website Photo Upload",

            {

                "fields": (

                    "website_upload_title",

                    "website_upload_description",

                ),

                "description": (

                    "These texts are displayed for the normal "
                    "website photo upload option."

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

                    "updated_at",

                ),

            },

        ),

    )


    # =====================================================
    # DISPLAY NAME
    # =====================================================

    @admin.display(
        description="Settings"
    )
    def settings_name(self, obj):

        return "Customization Settings"


    # =====================================================
    # LINK CONFIGURED?
    # =====================================================

    @admin.display(
        boolean=True,
        description="WhatsApp Link"
    )
    def whatsapp_link_configured(self, obj):

        return bool(

            obj.whatsapp_chat_link

        )


    # =====================================================
    # ALLOW ONLY ONE SETTINGS OBJECT
    #
    # We only need one global CustomizationSettings record.
    #
    # Once one object exists:
    #
    # "Add Customization Setting"
    #
    # disappears from Django Admin.
    #
    # Admin can simply edit the existing object.
    #
    # =====================================================

    def has_add_permission(
        self,
        request
    ):

        if (

            CustomizationSettings
            .objects
            .exists()

        ):

            return False

        return super().has_add_permission(
            request
        )


    # =====================================================
    # PREVENT DELETION
    #
    # Once settings are created, we keep the record.
    #
    # Admin can disable WhatsApp using:
    #
    # whatsapp_enabled = False
    #
    # instead of deleting the settings.
    #
    # =====================================================

    def has_delete_permission(
        self,
        request,
        obj=None
    ):

        return False