import json
import re
import urllib.request
from difflib import SequenceMatcher

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from products.models import Product
from sitecontent.models import SiteSettings
from orders.models import Order
from coupons.models import Coupon
from offers.models import Offer

from .models import ChatConversation, ChatMessage


# ============================================================
# TEXT HELPERS
# ============================================================

def similarity(a, b):
    a = re.sub(r"[^a-z0-9 ]", " ", str(a or "").lower())
    b = re.sub(r"[^a-z0-9 ]", " ", str(b or "").lower())

    a = re.sub(r"\s+", " ", a).strip()
    b = re.sub(r"\s+", " ", b).strip()

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def _tokens(text):
    return re.findall(
        r"[a-z0-9]+",
        str(text or "").lower()
    )


# ============================================================
# PRODUCT INTENT
# ============================================================

PRODUCT_WORDS = {
    "product",
    "products",
    "shop",
    "buy",
    "price",
    "prices",
    "cost",
    "frame",
    "frames",
    "gift",
    "gifts",
    "photo",
    "photos",
    "custom",
    "customize",
    "customized",
    "customization",
    "album",
    "albums",
    "poster",
    "posters",
    "canvas",
    "mug",
    "mugs",
    "keychain",
    "keychains",
    "print",
    "prints",
    "available",
    "availability",
    "show",
    "looking",
    "find",
    "need",
    "want",
    "recommend",
    "suggest",
}


PRODUCT_PHRASES = [
    "show me",
    "show some",
    "show products",
    "show product",
    "looking for",
    "i am looking for",
    "i'm looking for",
    "i want",
    "i need",
    "find me",
    "find some",
    "suggest me",
    "suggest some",
    "recommend me",
    "recommend some",
    "how much",
    "how much is",
    "how much does",
]


def is_product_query(message):
    """
    Detect product-related messages.

    Also checks actual product names so that small spelling
    mistakes can still trigger product search.
    """

    text = str(message or "").lower().strip()

    if not text:
        return False

    # Normal greetings should NOT trigger product search.
    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hai",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
    }

    if text in greetings:
        return False

    words = set(_tokens(text))

    # Normal product keywords.
    if words.intersection(PRODUCT_WORDS):
        return True

    # Product-related phrases.
    if any(
        phrase in text
        for phrase in PRODUCT_PHRASES
    ):
        return True

    # --------------------------------------------------------
    # TYPO-TOLERANT PRODUCT NAME DETECTION
    # --------------------------------------------------------

    try:
        products = Product.objects.filter(
            active=True
        ).only(
            "name",
            "slug"
        )

        message_words = _tokens(text)

        for product in products:

            product_name = str(
                getattr(product, "name", "")
            ).lower().strip()

            if not product_name:
                continue

            # Whole message similarity.
            if similarity(text, product_name) >= 0.45:
                return True

            product_words = _tokens(
                product_name
            )

            # Compare every user word with every product word.
            for user_word in message_words:

                for product_word in product_words:

                    if len(user_word) < 2:
                        continue

                    if similarity(
                        user_word,
                        product_word
                    ) >= 0.68:
                        return True

    except Exception:
        pass

    return False


# ============================================================
# SIMILAR PRODUCTS
# ============================================================

def find_similar_products(
    message,
    limit=6
):
    """
    Find products using fuzzy matching.

    Examples:

        photo frme
        phoot frme
        photo fram
        custmized photo
        birthdy gift

    can find the closest products.
    """

    query = str(
        message or ""
    ).lower().strip()

    if not query:
        return []

    query_tokens = _tokens(query)

    if not query_tokens:
        return []

    products = Product.objects.filter(
        active=True
    ).order_by(
        "-featured",
        "-created_at"
    )

    scored = []

    for product in products:

        name = str(
            getattr(product, "name", "")
            or ""
        )

        slug = str(
            getattr(product, "slug", "")
            or ""
        )

        description = str(
            getattr(product, "description", "")
            or ""
        )

        # Try to include category safely.
        category_name = ""

        try:
            category = getattr(
                product,
                "category",
                None
            )

            if category:
                category_name = str(
                    getattr(
                        category,
                        "name",
                        ""
                    )
                    or ""
                )
        except Exception:
            category_name = ""

        searchable = " ".join([
            name,
            slug,
            category_name,
            description,
        ]).lower()

        searchable_tokens = _tokens(
            searchable
        )

        # ----------------------------------------------------
        # Whole query vs product name.
        # ----------------------------------------------------

        name_score = similarity(
            query,
            name
        )

        score = name_score

        # ----------------------------------------------------
        # Individual words.
        # ----------------------------------------------------

        matched_words = 0

        for user_word in query_tokens:

            best_word_score = 0.0

            for target_word in searchable_tokens:

                current = similarity(
                    user_word,
                    target_word
                )

                if current > best_word_score:
                    best_word_score = current

            if best_word_score >= 0.55:
                matched_words += 1

            score = max(
                score,
                best_word_score * 0.90
            )

        # ----------------------------------------------------
        # Coverage.
        # ----------------------------------------------------

        if query_tokens:

            coverage = (
                matched_words /
                len(query_tokens)
            )

            score = max(
                score,
                0.35 + (
                    coverage * 0.55
                )
            )

        # ----------------------------------------------------
        # Direct substring.
        # ----------------------------------------------------

        if query in searchable:
            score = max(
                score,
                0.95
            )

        # ----------------------------------------------------
        # Exact product name.
        # ----------------------------------------------------

        if query == name.lower().strip():
            score = 1.0

        # ----------------------------------------------------
        # Keep reasonably relevant products.
        # ----------------------------------------------------

        if score >= 0.35:
            scored.append(
                (
                    score,
                    product
                )
            )

    # Highest score first.
    scored.sort(
        key=lambda item: (
            -item[0],
            -int(
                bool(
                    getattr(
                        item[1],
                        "featured",
                        False
                    )
                )
            )
        )
    )

    return [
        product
        for score, product
        in scored[:limit]
    ]


# ============================================================
# PRODUCT LINKS
# ============================================================

def _product_links(products):

    links = []

    for product in products:

        try:
            url = reverse(
                "products:detail",
                args=[product.slug]
            )
        except Exception:
            url = "/products/"

        links.append({
            "label": product.name,
            "price": str(product.price),
            "url": url,
        })

    return links


# ============================================================
# PRODUCT SUGGESTIONS
# ============================================================

def _product_suggestions(products):

    suggestions = []

    for product in products:

        suggestions.append({
            "name": product.name,
            "slug": product.slug,
        })

    return suggestions


# ============================================================
# USER + STORE CONTEXT
# ============================================================

def _user_context(
    user,
    relevant_products=None,
    include_products=False
):

    now = timezone.now()

    lines = []

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    if include_products:

        products = (
            relevant_products
            if relevant_products is not None
            else Product.objects.filter(
                active=True
            ).order_by(
                "-featured",
                "-created_at"
            )[:40]
        )

        if products:

            lines.append(
                "RELEVANT PRODUCTS:"
            )

            for product in products:

                try:
                    url = reverse(
                        "products:detail",
                        args=[product.slug]
                    )
                except Exception:
                    url = "/products/"

                lines.append(
                    f"- {product.name} | "
                    f"price=₹{product.price} | "
                    f"original_price="
                    f"₹{product.original_price or product.price} | "
                    f"stock={product.stock} | "
                    f"customizable={product.customizable} | "
                    f"url={url}"
                )

    # --------------------------------------------------------
    # OFFERS
    # --------------------------------------------------------

    try:
        offers = Offer.visible_for(user)
    except Exception:
        offers = []

    if offers:

        lines.append(
            "CURRENT OFFERS:"
        )

        for offer in offers[:20]:

            lines.append(
                f"- {offer.title} | "
                f"{offer.discount_text} | "
                f"{offer.description} | "
                f"CTA={offer.cta_text} | "
                f"url={offer.cta_url or '/products/'}"
            )

    # --------------------------------------------------------
    # COUPONS
    # --------------------------------------------------------

    coupons = Coupon.objects.filter(
        active=True,
        start_date__lte=now,
        expiry_date__gte=now
    )[:30]

    valid_coupons = []

    for coupon in coupons:

        try:
            valid = coupon.is_valid_now()[0]
        except Exception:
            valid = False

        if valid:
            valid_coupons.append(
                coupon
            )

    if valid_coupons:

        lines.append(
            "CURRENT COUPONS:"
        )

        for coupon in valid_coupons:

            if coupon.discount_type == "percentage":
                discount = (
                    f"{coupon.discount_value}%"
                )
            else:
                discount = (
                    f"₹{coupon.discount_value} OFF"
                )

            lines.append(
                f"- code={coupon.code} | "
                f"discount={discount} | "
                f"minimum_order="
                f"₹{coupon.minimum_order} | "
                f"maximum_discount="
                f"{coupon.maximum_discount or 'none'} | "
                f"expiry="
                f"{coupon.expiry_date:%d %b %Y}"
            )

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    if user and user.is_authenticated:

        lines.append(
            "LOGGED-IN CUSTOMER:"
        )

        lines.append(
            f"name="
            f"{getattr(user, 'display_name', '')} | "
            f"username="
            f"{getattr(user, 'username', '')} | "
            f"email="
            f"{getattr(user, 'email', '')} | "
            f"phone="
            f"{getattr(user, 'phone', '')}"
        )

        orders = Order.objects.filter(
            user=user
        ).order_by(
            "-created_at"
        )[:10]

        lines.append(
            "CUSTOMER ORDERS:"
        )

        for order in orders:

            try:
                status = (
                    order.get_status_display()
                )
            except Exception:
                status = str(
                    getattr(
                        order,
                        "status",
                        "Unknown"
                    )
                )

            lines.append(
                f"- #{order.order_number} | "
                f"status={status} | "
                f"total=₹{order.grand_total} | "
                f"date="
                f"{order.created_at:%d %b %Y}"
            )

    else:

        lines.append(
            "CUSTOMER: Visitor is not logged in. "
            "Never invent private customer data."
        )

    return "\n".join(lines)


# ============================================================
# FALLBACK RESPONSE
# ============================================================

def _fallback_reply(
    message,
    user=None,
    relevant_products=None
):

    text = str(
        message or ""
    ).lower().strip()

    name = (
        getattr(
            user,
            "display_name",
            ""
        )
        if user
        and user.is_authenticated
        else "there"
    )

    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    if text in {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hai",
    }:

        return (
            f"Hi {name} 👋 "
            "I’m Hopy, your Digital Galleria "
            "assistant. Ask me anything about "
            "products, prices, offers, coupons, "
            "orders, customization, payment or delivery."
        )

    # --------------------------------------------------------
    # ORDER
    # --------------------------------------------------------

    if (
        user
        and user.is_authenticated
        and any(
            word in text
            for word in [
                "order",
                "track",
                "tracking",
                "status",
            ]
        )
    ):

        order = Order.objects.filter(
            user=user
        ).order_by(
            "-created_at"
        ).first()

        if order:

            return (
                f"Sure {name} — your latest order "
                f"#{order.order_number} is currently "
                f"{order.get_status_display()}. "
                f"Total ₹{order.grand_total}."
            )

        return (
            f"{name}, I checked your account and "
            "you don’t have an order yet."
        )

    # --------------------------------------------------------
    # COUPON
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "coupon",
            "promo",
            "discount code",
            "coupon code",
        ]
    ):

        coupons = Coupon.objects.filter(
            active=True,
            start_date__lte=timezone.now(),
            expiry_date__gte=timezone.now()
        )

        valid = []

        for coupon in coupons:

            try:
                if coupon.is_valid_now()[0]:
                    valid.append(
                        coupon
                    )
            except Exception:
                pass

        if valid:

            return (
                "Here are the currently active coupons: "
                + " • ".join(
                    f"{coupon.code} — "
                    f"{coupon.discount_value}"
                    f"{'%' if coupon.discount_type == 'percentage' else ' off'}"
                    for coupon in valid
                )
            )

        return (
            "There are no active coupons available "
            "right now."
        )

    # --------------------------------------------------------
    # OFFERS
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "offer",
            "offers",
            "sale",
            "deal",
            "deals",
        ]
    ):

        try:
            offers = Offer.visible_for(
                user
            )
        except Exception:
            offers = []

        if offers:

            return (
                "Current offers: "
                + " • ".join(
                    f"{offer.title} — "
                    f"{offer.discount_text}"
                    for offer in offers[:8]
                )
            )

        return (
            "There are no active offers right now."
        )

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    if is_product_query(message):

        products = (
            relevant_products
            if relevant_products is not None
            else find_similar_products(
                message,
                limit=6
            )
        )

        if products:

            return (
                "Sure 😊 I found these products "
                "that may match what you mean: "
                + " • ".join(
                    f"{product.name} — ₹{product.price}"
                    for product in products
                )
            )

        return (
            "I couldn't find an exact match. "
            "Try another product name and I'll "
            "help you find it 😊"
        )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "pay",
            "payment",
            "upi",
            "qr",
            "screenshot",
        ]
    ):

        site_settings = SiteSettings.load()

        return (
            "We use manual UPI payment. "
            f"UPI ID: "
            f"{site_settings.upi_id or 'not configured'}. "
            "After paying, upload your payment screenshot."
        )

    # --------------------------------------------------------
    # CUSTOMIZATION
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "custom",
            "customize",
            "customization",
            "photo upload",
            "image upload",
        ]
    ):

        return (
            "Open a customizable product, choose "
            "Customize, upload your original photos "
            "and continue to checkout."
        )

    # --------------------------------------------------------
    # DELIVERY
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "deliver",
            "delivery",
            "shipping",
            "ship",
        ]
    ):

        return (
            "Delivery charges are calculated from "
            "the products in your cart and shown "
            "at checkout."
        )

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return (
        "I’m Hopy, your Digital Galleria assistant. "
        "Ask me naturally — I can help with products, "
        "prices, offers, coupons, customization, "
        "payment, delivery and your account."
    )


# ============================================================
# OPENAI RESPONSE
# ============================================================

def _ai_reply(
    message,
    user,
    conversation,
    relevant_products=None
):

    api_key = getattr(
        settings,
        "OPENAI_API_KEY",
        ""
    )

    if not api_key:

        return _fallback_reply(
            message,
            user,
            relevant_products
        )

    product_query = is_product_query(
        message
    )

    history = list(
        conversation.messages.order_by(
            "-created_at"
        )[:12]
    )

    history.reverse()

    system_prompt = """
You are Hopy, the friendly, natural Digital Galleria personal concierge.

Speak like a helpful human assistant.

Understand:
- English
- Malayalam
- Manglish
- Casual typing
- Small spelling mistakes

Use the currently logged-in customer's real account
information when relevant.

Never invent:
- orders
- payment status
- addresses
- phone numbers
- private information
- prices
- coupons
- offers
- policies

Only provide customer-specific information belonging to
the currently logged-in customer.

Use the supplied live store context for:
- products
- exact product names
- exact prices
- stock
- customization
- offers
- coupons
- orders

If the user makes spelling mistakes, infer their intended
meaning using the supplied product context.

When recommending products, use the exact product names
and URLs supplied by the system.

Do not list products for simple greetings.

Keep replies concise but useful.

Address the customer naturally by name when appropriate.
"""

    context = _user_context(
        user=user,
        relevant_products=relevant_products,
        include_products=product_query
    )

    messages = [
        {
            "role": "system",
            "content": (
                system_prompt
                + "\n\nSTORE + CUSTOMER CONTEXT:\n"
                + context
            ),
        }
    ]

    for item in history:

        messages.append({
            "role": (
                "user"
                if item.role == "user"
                else "assistant"
            ),
            "content": item.content,
        })

    messages.append({
        "role": "user",
        "content": message,
    })

    payload = json.dumps({
        "model": getattr(
            settings,
            "OPENAI_MODEL",
            "gpt-4o-mini"
        ),
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 500,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type":
                "application/json",

            "Authorization":
                f"Bearer {api_key}",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            req,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        return (
            data[
                "choices"
            ][0][
                "message"
            ][
                "content"
            ].strip()
        )

    except Exception:

        return _fallback_reply(
            message,
            user,
            relevant_products
        )


# ============================================================
# CHATBOT API
# ============================================================

@require_POST
def chatbot_reply(request):

    message = request.POST.get(
        "message",
        ""
    ).strip()

    # --------------------------------------------------------
    # Empty message
    # --------------------------------------------------------

    if not message:

        return JsonResponse({
            "reply":
                "Tell me what you need and I’ll help 😊",

            "links": [],

            "suggestions": [],
        })

    # --------------------------------------------------------
    # PRODUCT DETECTION
    # --------------------------------------------------------

    product_query = is_product_query(
        message
    )

    relevant_products = []

    if product_query:

        relevant_products = find_similar_products(
            message,
            limit=6
        )

    # --------------------------------------------------------
    # SUGGESTIONS
    # --------------------------------------------------------

    suggestions = []

    if (
        product_query
        and relevant_products
    ):

        normalized_message = re.sub(
            r"[^a-z0-9]+",
            " ",
            message.lower()
        ).strip()

        exact_match = False

        for product in relevant_products:

            normalized_name = re.sub(
                r"[^a-z0-9]+",
                " ",
                product.name.lower()
            ).strip()

            if (
                normalized_message
                == normalized_name
            ):
                exact_match = True
                break

        # If it is not an exact product name,
        # provide suggestions.
        if not exact_match:

            suggestions = _product_suggestions(
                relevant_products[:5]
            )

    # --------------------------------------------------------
    # LOGGED-IN CHAT
    # --------------------------------------------------------

    if request.user.is_authenticated:

        conversation_id = request.session.get(
            "dg_chat_conversation_id"
        )

        conversation = None

        if conversation_id:

            conversation = (
                ChatConversation.objects.filter(
                    id=conversation_id,
                    user=request.user
                ).first()
            )

        if not conversation:

            conversation = (
                ChatConversation.objects.create(
                    user=request.user,
                    title=message[:80]
                )
            )

            request.session[
                "dg_chat_conversation_id"
            ] = conversation.id

        ChatMessage.objects.create(
            conversation=conversation,
            role="user",
            content=message
        )

        reply = _ai_reply(
            message,
            request.user,
            conversation,
            relevant_products
        )

        ChatMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=reply
        )

    else:

        reply = _fallback_reply(
            message,
            request.user,
            relevant_products
        )

    # --------------------------------------------------------
    # LINKS
    # --------------------------------------------------------

    links = []

    # Product links only for product queries.
    if (
        product_query
        and relevant_products
    ):

        links.extend(
            _product_links(
                relevant_products
            )
        )

    # --------------------------------------------------------
    # OFFER LINKS
    # --------------------------------------------------------

    lowered = message.lower()

    if any(
        keyword in lowered
        for keyword in [
            "offer",
            "offers",
            "sale",
            "deal",
            "deals",
        ]
    ):

        try:

            offers = Offer.visible_for(
                request.user
            )

            for offer in offers[:6]:

                links.append({
                    "label":
                        f"{offer.title} — "
                        f"{offer.discount_text}",

                    "url":
                        offer.cta_url
                        or "/products/",
                })

        except Exception:
            pass

    # --------------------------------------------------------
    # FINAL JSON
    # --------------------------------------------------------

    return JsonResponse({
        "reply": reply,

        "links": links[:8],

        "suggestions": suggestions[:5],
    })