"""
Live-data intent handlers for Hopy (the site chatbot).

Every answer here is derived from the real database at request time — no
hard-coded products, prices, offers, colours, or delivery figures. Anything
user-specific (orders, cart, account) is always scoped to request.user, never
to an ID supplied by the message text, so one user can never see another
user's data through the chatbot.
"""
import re
from decimal import Decimal, InvalidOperation
from django.urls import reverse

from products.models import Product, Colour, ProductVariant
from categories.models import Category
from products.services.search import search_products, _best_token_similarity

_STOPWORDS = {
    "do", "you", "have", "any", "a", "an", "the", "for", "is", "are", "looking",
    "want", "need", "please", "can", "i", "me", "to", "of", "in", "on", "with",
    "show", "products", "product", "under", "below", "colour", "color", "colours",
    "colors", "available",
}


def try_greeting(request, text):
    """General small-talk fallback — 'hello' should feel like talking to an
    assistant, not hit a rigid 'no match' response. Uses the real logged-in
    name when available; never a placeholder name."""
    lower = text.strip().lower().strip("!.?")
    greetings = {"hi", "hello", "hey", "hii", "hiya", "good morning", "good afternoon", "good evening", "namaste", "yo"}
    thanks = {"thanks", "thank you", "thankyou", "thx", "ty"}
    farewells = {"bye", "goodbye", "see you", "cya"}
    how_are_you = {"how are you", "how are you?", "how r u", "whats up", "what's up", "sup"}

    if lower in how_are_you:
        return "I'm doing great, thanks for asking! How can I help you shop today?"
    if lower in greetings or any(lower.startswith(g + " ") for g in greetings):
        name = request.user.name.split()[0] if request.user.is_authenticated and request.user.name else None
        if name:
            return f"Hey {name}! 👋 I'm Hopy. I can help you find products, check your orders, track a delivery, or set up a customization — what would you like to do?"
        return "Hey there! 👋 I'm Hopy. I can help you find products, check offers, or track an order — what would you like to do?"
    if lower in thanks:
        return "You're welcome! Let me know if there's anything else I can help with."
    if lower in farewells:
        return "See you soon! Happy shopping. 👋"
    return None


def product_url(product, colour_name=None):
    """Real Django URL reversing — never a fabricated link."""
    url = reverse("products:detail", kwargs={"slug": product.slug})
    if colour_name:
        url += f"?colour={colour_name.lower().replace(' ', '-')}"
    return url


def _active_colours():
    return list(Colour.objects.filter(active=True))


def _extract_price_ceiling(text):
    """'under 1000' / 'below ₹500' / 'under Rs 750' -> Decimal(1000) etc."""
    m = re.search(r"(?:under|below|less than)\s*(?:rs\.?|₹)?\s*(\d+)", text, re.IGNORECASE)
    if not m:
        return None
    try:
        return Decimal(m.group(1))
    except InvalidOperation:
        return None


def _extract_colour_mentions(text):
    """Matches against the REAL, admin-managed Colour list — never a hard-coded palette."""
    lower = text.lower()
    found = []
    for colour in _active_colours():
        if re.search(rf"\b{re.escape(colour.name.lower())}\b", lower):
            found.append(colour)
    return found


def _extract_category_mentions(text):
    lower = text.lower()
    found = []
    for cat in Category.objects.filter(active=True):
        name = cat.name.lower()
        if name in lower or name.rstrip("s") in lower:
            found.append(cat)
    return found


def try_colour_or_filtered_search(text):
    """
    Handles: 'black products', 'red shirts', 'red products under 1000',
    'show black nike', 'featured products', 'new products'.
    Returns (reply_text, products) or None if this isn't that kind of query.
    """
    lower = text.lower()
    colours = _extract_colour_mentions(text)
    categories = _extract_category_mentions(text)
    price_ceiling = _extract_price_ceiling(text)
    wants_featured = "featured" in lower
    wants_new = "new" in lower and "product" in lower

    if not (colours or categories or price_ceiling is not None or wants_featured or wants_new):
        return None

    qs = Product.objects.filter(active=True)
    if categories:
        qs = qs.filter(category__in=categories)
    if wants_featured:
        qs = qs.filter(featured=True)
    if wants_new:
        qs = qs.order_by("-created_date")
    if price_ceiling is not None:
        qs = qs.filter(price__lte=price_ceiling)

    products = list(qs.distinct()[:8])

    if colours:
        # Colour is a variant-level attribute — filter via ProductVariant, then
        # map back to distinct products so links can carry the right ?colour=.
        variant_qs = ProductVariant.objects.filter(active=True, colour__in=colours, product__active=True)
        if categories:
            variant_qs = variant_qs.filter(product__category__in=categories)
        if price_ceiling is not None:
            variant_qs = variant_qs.filter(product__price__lte=price_ceiling)
        variants = list(variant_qs.select_related("product", "colour").distinct()[:8])
        if not variants:
            colour_names = ", ".join(c.name for c in colours)
            return (f"I couldn't find any products in {colour_names} right now.", [])
        seen = set()
        results = []
        for v in variants:
            if v.product_id in seen:
                continue
            seen.add(v.product_id)
            results.append({"product": v.product, "colour": v.colour})
        colour_names = ", ".join(c.name for c in colours)
        return (f"Here's what I found in {colour_names}:", results)

    if not products:
        return ("I couldn't find any matching products right now.", [])
    return ("Here's what I found:", [{"product": p, "colour": None} for p in products])


def try_product_colour_availability(text):
    """'What colours are available for Classic Shirt?' -> live variant list for that product."""
    lower = text.lower()
    if "colour" not in lower and "color" not in lower:
        return None
    if not any(k in lower for k in ["available", "come in", "options", "which colour", "what colour"]):
        return None

    words = [w.strip("?.,!") for w in text.split() if w.strip("?.,!").lower() not in _STOPWORDS and len(w) > 2]
    candidate = " ".join(words)
    matches = search_products(candidate, limit=3) if candidate else []
    if not matches:
        return None
    product = matches[0]
    variants = product.active_variants()
    if not variants:
        return (f"{product.name} doesn't have colour options — it's available in a single version.", [])
    colour_list = ", ".join(v.colour.name for v in variants)
    return (f"{product.name} is available in: {colour_list}.", [{"product": product, "colour": v.colour} for v in variants])


def try_show_specific_colour(text):
    """'Show red Classic Shirt' -> single product, specific colour, direct link.
    Deliberately does NOT fire for '<colour> <category>' phrasing like 'red shirts' —
    that's a filtered listing (try_colour_or_filtered_search), not one specific product."""
    colours = _extract_colour_mentions(text)
    if not colours:
        return None
    category_names = {c.name.lower() for c in Category.objects.filter(active=True)}
    words = [w.strip("?.,!") for w in text.split() if w.strip("?.,!").lower() not in _STOPWORDS
             and w.lower() not in {c.name.lower() for c in colours} and len(w) > 2]
    candidate = " ".join(words)
    if not candidate:
        return None
    if candidate.lower() in category_names or candidate.lower().rstrip("s") in category_names:
        return None
    matches = search_products(candidate, limit=3)
    if not matches:
        return None
    product = matches[0]
    variant = product.get_variant_by_colour_slug(colours[0].name)
    if not variant:
        return (f"{product.name} isn't currently available in {colours[0].name}.", [])
    return (f"Here's {product.name} in {colours[0].name}:", [{"product": product, "colour": variant.colour}])


def try_order_colour(request, text):
    """'What colour did I order?' — answered strictly from the historical OrderItem
    snapshot (never from live ProductVariant data, since the admin may have since
    changed the product), and strictly scoped to request.user."""
    if not request.user.is_authenticated:
        return None
    lower = text.lower()
    if not (("colour" in lower or "color" in lower) and ("order" in lower or "i order" in lower)):
        return None
    from orders.models import Order
    order = Order.objects.filter(user=request.user).order_by("-created_date").first()
    if not order:
        return "You don't have any orders yet."
    lines = []
    for item in order.items.all():
        if item.colour_name_snapshot:
            lines.append(f"{item.product_name_snapshot} — Colour: {item.colour_name_snapshot} (SKU: {item.sku_snapshot}) × {item.quantity}")
        else:
            lines.append(f"{item.product_name_snapshot} × {item.quantity}")
    body = "\n".join(lines)
    return f"Order {order.order_number}:\n{body}"


def try_my_cart(request, text):
    lower = text.lower()
    if "my cart" not in lower and "what's in my cart" not in lower and "whats in my cart" not in lower:
        return None
    from cart.cart import Cart
    lines = Cart(request).get_lines()
    if not lines:
        return "Your cart is empty."
    parts = []
    for l in lines:
        label = l["product"].name
        if l["variant"]:
            label += f" ({l['variant'].colour.name})"
        parts.append(f"{label} × {l['quantity']} — ₹{l['line_total']}")
    return "Your cart:\n" + "\n".join(parts)


def try_my_details(request, text):
    lower = text.lower()
    if not any(k in lower for k in ["my details", "my account", "my profile", "my info"]):
        return None
    if not request.user.is_authenticated:
        return "Please log in to view your account details."
    u = request.user
    return f"Name: {u.name}\nEmail: {u.email}\nPhone: {u.phone or 'Not set'}"


def try_offers(text):
    lower = text.lower()
    if not any(k in lower for k in ["offer", "discount", "coupon", "promo"]):
        return None
    from django.utils import timezone
    from coupons.models import Coupon
    now = timezone.now()
    active = Coupon.objects.filter(active=True, start_date__lte=now, expiry_date__gte=now)
    if not active.exists():
        return "There are no active offers right now — check back soon!"
    parts = []
    for c in active[:6]:
        if c.discount_type == "percentage":
            parts.append(f"{c.code}: {c.discount_value}% off (min order ₹{c.minimum_order})")
        else:
            parts.append(f"{c.code}: ₹{c.discount_value} off (min order ₹{c.minimum_order})")
    return "Current offers:\n" + "\n".join(parts)


def try_show_categories(text):
    lower = text.lower()
    if "categor" not in lower:
        return None
    cats = Category.objects.filter(active=True)
    if not cats.exists():
        return "No categories are configured yet."
    return "Categories: " + ", ".join(c.name for c in cats)


def try_customize(text):
    lower = text.lower()
    if "customi" not in lower:
        return None
    return ("You can customize any product marked 'Customizable' — open the product page and tap "
            "Start Customizing, or customize directly from an item already in your Cart.")
