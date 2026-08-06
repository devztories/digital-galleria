from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse

from django.db.models import (
    Q,
    Case,
    When,
    Value,
    IntegerField,
)


# =========================================================
# MODELS
# =========================================================

from .models import Product

from categories.models import Category

from orders.models import (
    ProductCustomization,
    ProductCustomizationImage,
)

from homepage.models import (
    Advertisement,
    SocialMediaLink,
    AboutSection,
    CustomizationSettings,
)


# =========================================================
# HOME PAGE
# =========================================================

def home(request):

    # =====================================================
    # CATEGORIES
    # =====================================================

    categories = (
        Category.objects
        .all()
        .order_by("name")
    )

    # =====================================================
    # SEARCH QUERY
    # =====================================================

    search_query = (
        request.GET.get(
            "search",
            ""
        ).strip()
    )

    # =====================================================
    # CATEGORY FILTER
    # =====================================================

    category_id = (
        request.GET.get(
            "category",
            ""
        ).strip()
    )

    selected_category = None

    # =====================================================
    # BASE PRODUCT QUERY
    # =====================================================

    products = (
        Product.objects
        .select_related("category")
        .all()
    )

    # =====================================================
    # APPLY CATEGORY FILTER
    # =====================================================

    if category_id:

        try:

            selected_category = (
                Category.objects.get(
                    id=int(category_id)
                )
            )

            products = products.filter(
                category=selected_category
            )

        except (
            ValueError,
            TypeError,
            Category.DoesNotExist,
        ):

            selected_category = None
            category_id = ""

    # =====================================================
    # SMART SEARCH
    # =====================================================

    if search_query:

        products = (
            products

            .filter(
                Q(
                    name__icontains=search_query
                )
                |
                Q(
                    category__name__icontains=
                    search_query
                )
            )

            .annotate(

                search_priority=Case(

                    When(
                        name__istartswith=
                        search_query,
                        then=Value(1),
                    ),

                    When(
                        name__icontains=
                        search_query,
                        then=Value(2),
                    ),

                    When(
                        category__name__istartswith=
                        search_query,
                        then=Value(3),
                    ),

                    When(
                        category__name__icontains=
                        search_query,
                        then=Value(4),
                    ),

                    default=Value(5),

                    output_field=
                    IntegerField(),

                )
            )

            .order_by(
                "search_priority",
                "name",
            )
        )

    else:

        products = products.order_by(
            "name"
        )

    # =====================================================
    # CURRENT TIME
    # =====================================================

    now = timezone.now()

    # =====================================================
    # ACTIVE ADS
    # =====================================================

    active_ads = (
        Advertisement.objects

        .filter(
            is_active=True
        )

        .filter(
            Q(
                start_at__isnull=True
            )
            |
            Q(
                start_at__lte=now
            )
        )

        .filter(
            Q(
                end_at__isnull=True
            )
            |
            Q(
                end_at__gte=now
            )
        )
    )

    # =====================================================
    # TEXT ADS
    # =====================================================

    text_ads = (
        active_ads
        .filter(
            ad_type="text"
        )
        .exclude(
            text=""
        )
        .order_by(
            "-created_at"
        )
    )

    # =====================================================
    # IMAGE AD
    # =====================================================

    image_ad = (
        active_ads
        .filter(
            ad_type="image"
        )
        .exclude(
            image=""
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    # =====================================================
    # SOCIAL MEDIA LINKS
    # =====================================================

    social_links = (
        SocialMediaLink.objects
        .filter(
            is_active=True
        )
        .order_by(
            "platform"
        )
    )

    # =====================================================
    # ABOUT SECTION
    # =====================================================

    about_section = (
        AboutSection.objects
        .filter(
            is_active=True
        )
        .order_by(
            "-updated_at"
        )
        .first()
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "categories":
        categories,

        "selected_category":
        selected_category,

        "selected_category_id":
        category_id,

        "products":
        products,

        "search_query":
        search_query,

        "text_ads":
        text_ads,

        "image_ad":
        image_ad,

        "social_links":
        social_links,

        "about_section":
        about_section,

    }

    return render(
        request,
        "home.html",
        context
    )


# =========================================================
# LIVE PRODUCT SEARCH
# =========================================================

def product_search_suggestions(request):

    query = (
        request.GET.get(
            "q",
            ""
        ).strip()
    )

    if not query:

        return JsonResponse(
            {
                "results": []
            }
        )

    query = query[:100]

    products = (

        Product.objects

        .select_related(
            "category"
        )

        .filter(

            Q(
                name__icontains=query
            )

            |

            Q(
                category__name__icontains=query
            )

        )

        .annotate(

            search_priority=Case(

                When(
                    name__istartswith=query,
                    then=Value(1),
                ),

                When(
                    name__icontains=query,
                    then=Value(2),
                ),

                When(
                    category__name__istartswith=query,
                    then=Value(3),
                ),

                When(
                    category__name__icontains=query,
                    then=Value(4),
                ),

                default=Value(5),

                output_field=IntegerField(),

            )
        )

        .order_by(
            "search_priority",
            "name",
        )

        [:8]

    )

    results = []

    for product in products:

        image_url = ""

        if product.image:

            try:

                image_url = (
                    product.image.url
                )

            except (
                ValueError,
                AttributeError,
            ):

                image_url = ""

        category_name = ""

        if product.category:

            category_name = (
                product.category.name
            )

        in_stock = (

            product.stock > 0

            and

            product.stock_status
            == "In Stock"

        )

        results.append(

            {

                "id":
                product.id,

                "name":
                product.name,

                "price":
                str(product.price),

                "category":
                category_name,

                "image":
                image_url,

                "in_stock":
                in_stock,

                "is_customizable":
                product.is_customizable,

            }

        )

    return JsonResponse(

        {

            "results":
            results,

            "query":
            query,

        }

    )


# =========================================================
# PRODUCT DETAIL
# =========================================================

def product_detail(
    request,
    product_id
):

    product = get_object_or_404(

        Product.objects
        .select_related(
            "category"
        ),

        id=product_id

    )

    related_products = (

        Product.objects

        .filter(
            category=product.category
        )

        .exclude(
            id=product.id
        )

        .order_by(
            "name"
        )

        [:4]

    )

    return render(

        request,

        "product/product_details.html",

        {

            "product":
            product,

            "related_products":
            related_products,

        }

    )


# =========================================================
# CUSTOMIZATION HELPERS
# =========================================================

def get_max_customization_images(
    product,
    quantity=1,
):

    """
    Calculate maximum number of images allowed.

    SINGLE:
        Always 1 image.

    MULTIPLE + quantity based:
        Quantity determines image limit.

    MULTIPLE + admin limit:
        Uses max_customization_images.
    """

    upload_mode = getattr(
        product,
        "customization_upload_mode",
        "single",
    )

    # =====================================================
    # SINGLE IMAGE PRODUCT
    # =====================================================

    if upload_mode == "single":

        return 1

    # =====================================================
    # QUANTITY BASED IMAGE LIMIT
    # =====================================================

    if getattr(
        product,
        "image_limit_based_on_quantity",
        False,
    ):

        try:

            quantity = int(quantity)

        except (
            TypeError,
            ValueError,
        ):

            quantity = 1

        return max(
            quantity,
            1,
        )

    # =====================================================
    # ADMIN DEFINED IMAGE LIMIT
    # =====================================================

    try:

        maximum = int(

            getattr(
                product,
                "max_customization_images",
                1,
            )

            or 1

        )

    except (
        TypeError,
        ValueError,
    ):

        maximum = 1

    return max(
        maximum,
        1,
    )


# =========================================================
# GET CUSTOMIZATION SETTINGS
#
# Only one settings record is expected.
#
# If admin has not created settings yet:
#
# customization_settings = None
#
# In that case:
#
# - Website upload still works.
# - WhatsApp option stays unavailable.
#
# =========================================================

def get_customization_settings():

    return (

        CustomizationSettings.objects
        .order_by(
            "-updated_at"
        )
        .first()

    )


# =========================================================
# BUILD CUSTOMIZATION PAGE CONTEXT
#
# Keeps all render responses consistent.
# =========================================================

def build_customization_context(
    product,
    quantity,
    max_images,
    customization_settings,
    error="",
    selected_method="website",
):

    whatsapp_available = False

    whatsapp_chat_link = ""

    # =====================================================
    # CHECK WHATSAPP CONFIGURATION
    # =====================================================

    if customization_settings:

        whatsapp_chat_link = (

            customization_settings
            .whatsapp_chat_link
            .strip()

        )

        whatsapp_available = (

            customization_settings
            .whatsapp_enabled

            and

            bool(
                whatsapp_chat_link
            )

        )

    return {

        "product":
        product,

        "quantity":
        quantity,

        "max_images":
        max_images,

        "customization_settings":
        customization_settings,

        "whatsapp_available":
        whatsapp_available,

        "whatsapp_chat_link":
        whatsapp_chat_link,

        "selected_method":
        selected_method,

        "error":
        error,

    }


# =========================================================
# CUSTOMIZE PRODUCT
#
# FINAL PHOTO SUBMISSION FLOW
#
#
# CUSTOMER CHOOSES:
#
# -----------------------------------------
#
# METHOD 1:
#
# WEBSITE UPLOAD
#
# Product
#     ↓
# Upload original image(s)
#     ↓
# Optional instructions
#     ↓
# Files saved
#     ↓
# Add customized product to cart
#
#
# -----------------------------------------
#
# METHOD 2:
#
# WHATSAPP
#
# Product
#     ↓
# Choose "Send Photos via WhatsApp"
#     ↓
# Open admin configured WhatsApp chat link
#     ↓
# Customer sends photos manually
#     ↓
# Customer returns to website
#     ↓
# Checks:
#
# "I have sent my photos via WhatsApp"
#
#     ↓
# Add customized product to cart
#
#
# IMPORTANT:
#
# WhatsApp confirmation is CUSTOMER DECLARATION only.
#
# It does not technically verify that the files were
# received by admin.
#
# Admin can later verify the WhatsApp photos manually.
#
# =========================================================

@login_required(
    login_url="login"
)
def customize_product(
    request,
    product_id
):

    # =====================================================
    # GET PRODUCT
    # =====================================================

    product = get_object_or_404(

        Product,

        id=product_id,

        is_customizable=True,

    )

    # =====================================================
    # QUANTITY
    # =====================================================

    quantity_value = (

        request.POST.get(
            "quantity"
        )

        if request.method == "POST"

        else request.GET.get(
            "quantity"
        )

    )

    try:

        quantity = int(
            quantity_value or 1
        )

    except (
        TypeError,
        ValueError,
    ):

        quantity = 1

    quantity = max(
        quantity,
        1,
    )

    # =====================================================
    # MAXIMUM ALLOWED IMAGES
    # =====================================================

    max_images = (

        get_max_customization_images(
            product,
            quantity,
        )

    )

    # =====================================================
    # CUSTOMIZATION SETTINGS
    # =====================================================

    customization_settings = (

        get_customization_settings()

    )

    # =====================================================
    # WHATSAPP AVAILABILITY
    # =====================================================

    whatsapp_chat_link = ""

    whatsapp_available = False

    if customization_settings:

        whatsapp_chat_link = (

            customization_settings
            .whatsapp_chat_link
            .strip()

        )

        whatsapp_available = (

            customization_settings
            .whatsapp_enabled

            and

            bool(
                whatsapp_chat_link
            )

        )

    # =====================================================
    # GET REQUEST
    # =====================================================

    if request.method == "GET":

        context = (

            build_customization_context(

                product=
                product,

                quantity=
                quantity,

                max_images=
                max_images,

                customization_settings=
                customization_settings,

                selected_method=
                "website",

            )

        )

        return render(

            request,

            "products/customize_product.html",

            context,

        )

    # =====================================================
    # CUSTOMER INSTRUCTIONS
    # =====================================================

    instructions = (

        request.POST.get(
            "instructions",
            ""
        ).strip()

    )

    # =====================================================
    # PHOTO SUBMISSION METHOD
    #
    # Expected:
    #
    # website
    #
    # OR
    #
    # whatsapp
    #
    # =====================================================

    submission_method = (

        request.POST.get(
            "submission_method",
            "website"
        )

        .strip()

        .lower()

    )

    # =====================================================
    # SECURITY:
    # ONLY ALLOW KNOWN METHODS
    # =====================================================

    if submission_method not in [

        "website",

        "whatsapp",

    ]:

        submission_method = "website"

    # =====================================================
    # WHATSAPP METHOD
    # =====================================================

    if submission_method == "whatsapp":

        # -------------------------------------------------
        # WHATSAPP MUST BE ENABLED BY ADMIN
        # -------------------------------------------------

        if not whatsapp_available:

            context = (

                build_customization_context(

                    product=
                    product,

                    quantity=
                    quantity,

                    max_images=
                    max_images,

                    customization_settings=
                    customization_settings,

                    selected_method=
                    "whatsapp",

                    error=(

                        "WhatsApp photo submission is "
                        "currently unavailable. Please "
                        "upload your photos directly "
                        "on the website."

                    ),

                )

            )

            return render(

                request,

                "products/customize_product.html",

                context,

            )

        # -------------------------------------------------
        # CUSTOMER CONFIRMATION CHECKBOX
        #
        # HTML checkbox:
        #
        # name="whatsapp_photos_confirmed"
        # value="yes"
        #
        # -------------------------------------------------

        whatsapp_confirmation = (

            request.POST.get(
                "whatsapp_photos_confirmed",
                ""
            )

            .strip()

            .lower()

        )

        if whatsapp_confirmation not in [

            "yes",

            "true",

            "1",

            "on",

        ]:

            context = (

                build_customization_context(

                    product=
                    product,

                    quantity=
                    quantity,

                    max_images=
                    max_images,

                    customization_settings=
                    customization_settings,

                    selected_method=
                    "whatsapp",

                    error=(

                        "Please confirm that you have "
                        "sent your customization photos "
                        "through WhatsApp before continuing."

                    ),

                )

            )

            return render(

                request,

                "products/customize_product.html",

                context,

            )

        # -------------------------------------------------
        # CREATE WHATSAPP CUSTOMIZATION
        #
        # No image is uploaded to website.
        #
        # original_image = None
        #
        # -------------------------------------------------

        customization = (

            ProductCustomization.objects.create(

                user=
                request.user,

                product=
                product,

                submission_method=
                "whatsapp",

                whatsapp_photos_confirmed=
                True,

                original_image=
                None,

                instructions=
                instructions,

                is_finalized=
                True,

            )

        )

        # -------------------------------------------------
        # REDIRECT TO CART
        # -------------------------------------------------

        add_to_cart_url = reverse(

            "add_customized_to_cart",

            kwargs={

                "product_id":
                product.id,

                "customization_id":
                customization.id,

            }

        )

        return redirect(

            f"{add_to_cart_url}"
            f"?quantity={quantity}"

        )

    # =====================================================
    # WEBSITE UPLOAD METHOD
    # =====================================================

    upload_mode = getattr(

        product,

        "customization_upload_mode",

        "single",

    )

    # =====================================================
    # GET UPLOADED IMAGES
    # =====================================================

    if upload_mode == "multiple":

        uploaded_images = (

            request.FILES.getlist(
                "customization_images"
            )

        )

    else:

        uploaded_images = []

        single_image = (

            request.FILES.get(
                "original_image"
            )

        )

        if single_image:

            uploaded_images = [

                single_image

            ]

    # =====================================================
    # IMAGE REQUIRED FOR WEBSITE METHOD
    # =====================================================

    if not uploaded_images:

        context = (

            build_customization_context(

                product=
                product,

                quantity=
                quantity,

                max_images=
                max_images,

                customization_settings=
                customization_settings,

                selected_method=
                "website",

                error=(

                    "Please upload at least one image."

                ),

            )

        )

        return render(

            request,

            "products/customize_product.html",

            context,

        )

    # =====================================================
    # SINGLE IMAGE SECURITY CHECK
    # =====================================================

    if (

        upload_mode == "single"

        and

        len(uploaded_images) != 1

    ):

        context = (

            build_customization_context(

                product=
                product,

                quantity=
                quantity,

                max_images=
                1,

                customization_settings=
                customization_settings,

                selected_method=
                "website",

                error=(

                    "This product accepts only one image."

                ),

            )

        )

        return render(

            request,

            "products/customize_product.html",

            context,

        )

    # =====================================================
    # MAXIMUM IMAGE LIMIT
    # =====================================================

    if len(
        uploaded_images
    ) > max_images:

        context = (

            build_customization_context(

                product=
                product,

                quantity=
                quantity,

                max_images=
                max_images,

                customization_settings=
                customization_settings,

                selected_method=
                "website",

                error=(

                    f"You can upload a maximum of "
                    f"{max_images} image(s)."

                ),

            )

        )

        return render(

            request,

            "products/customize_product.html",

            context,

        )

    # =====================================================
    # ALLOWED IMAGE TYPES
    # =====================================================

    allowed_types = [

        "image/jpeg",

        "image/png",

        "image/webp",

    ]

    # =====================================================
    # MAX FILE SIZE
    #
    # 10 MB PER IMAGE
    # =====================================================

    maximum_size = (

        10

        *

        1024

        *

        1024

    )

    # =====================================================
    # VALIDATE EVERY IMAGE
    # =====================================================

    for image in uploaded_images:

        # -------------------------------------------------
        # MIME TYPE
        # -------------------------------------------------

        content_type = getattr(

            image,

            "content_type",

            "",

        )

        if content_type not in allowed_types:

            context = (

                build_customization_context(

                    product=
                    product,

                    quantity=
                    quantity,

                    max_images=
                    max_images,

                    customization_settings=
                    customization_settings,

                    selected_method=
                    "website",

                    error=(

                        "Only JPG, PNG and WEBP "
                        "images are allowed."

                    ),

                )

            )

            return render(

                request,

                "products/customize_product.html",

                context,

            )

        # -------------------------------------------------
        # FILE SIZE
        # -------------------------------------------------

        if image.size > maximum_size:

            context = (

                build_customization_context(

                    product=
                    product,

                    quantity=
                    quantity,

                    max_images=
                    max_images,

                    customization_settings=
                    customization_settings,

                    selected_method=
                    "website",

                    error=(

                        f"{image.name} is larger "
                        f"than 10 MB."

                    ),

                )

            )

            return render(

                request,

                "products/customize_product.html",

                context,

            )

    # =====================================================
    # FIRST IMAGE
    #
    # Keep first image in original_image.
    #
    # Existing cart/admin/order compatibility.
    # =====================================================

    first_image = (

        uploaded_images[0]

    )

    # =====================================================
    # CREATE WEBSITE CUSTOMIZATION
    # =====================================================

    customization = (

        ProductCustomization.objects.create(

            user=
            request.user,

            product=
            product,

            submission_method=
            "website",

            whatsapp_photos_confirmed=
            False,

            original_image=
            first_image,

            instructions=
            instructions,

            is_finalized=
            True,

        )

    )

    # =====================================================
    # MULTIPLE IMAGE STORAGE
    #
    # original_image:
    #
    # First image for backwards compatibility.
    #
    # uploaded_images:
    #
    # Stores ALL uploaded images.
    #
    # =====================================================

    if upload_mode == "multiple":

        for position, image in enumerate(

            uploaded_images

        ):

            # -------------------------------------------------
            # RESET FILE POINTER
            #
            # The first image may already have been read while
            # saving original_image.
            # -------------------------------------------------

            try:

                image.seek(0)

            except (
                AttributeError,
                OSError,
            ):

                pass

            ProductCustomizationImage.objects.create(

                customization=
                customization,

                image=
                image,

                position=
                position,

            )

    # =====================================================
    # REDIRECT TO CART
    # =====================================================

    add_to_cart_url = reverse(

        "add_customized_to_cart",

        kwargs={

            "product_id":
            product.id,

            "customization_id":
            customization.id,

        }

    )

    return redirect(

        f"{add_to_cart_url}"
        f"?quantity={quantity}"

    )