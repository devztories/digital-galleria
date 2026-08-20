from django.http import JsonResponse
from django.views.decorators.http import require_POST

from products.models import Product
from products.services.search import search_products
from categories.models import Category
from .models import ChatConversation, ChatMessage
from .services import intents


def _get_conversation(request):
    conv_id = request.session.get("chat_conversation_id")
    if conv_id:
        conv = ChatConversation.objects.filter(id=conv_id).filter(user=request.user if request.user.is_authenticated else None).first()
        if conv:
            return conv
    conv = ChatConversation.objects.create(user=request.user if request.user.is_authenticated else None)
    request.session["chat_conversation_id"] = conv.id
    return conv


_STOPWORDS = {
    "do", "you", "have", "any", "a", "an", "the", "for", "is", "are", "looking",
    "want", "need", "please", "can", "i", "me", "to", "of", "in", "on", "with",
}


def _find_matching_products(text):
    """Typo-tolerant product matching, shared with the main search bar.
    Tries the full message first, then each significant word in it (so
    conversational phrasing like 'looking for a mug' still matches 'mug'),
    then falls back to matching category names (e.g. 'any frames?' -> Photo Frames)."""
    if not text or not text.strip():
        return []

    matches = search_products(text, limit=5)
    if matches:
        return matches

    words = [w.strip("?.,!") for w in text.lower().split()]
    words = [w for w in words if w and w not in _STOPWORDS and len(w) > 2]
    for word in words:
        matches = search_products(word, limit=5)
        if matches:
            return matches

    # Fall back: does any category name appear (fuzzily) in the message?
    from products.services.search import _best_token_similarity
    best_category, best_score = None, 0.0
    for cat in Category.objects.filter(active=True):
        score = _best_token_similarity(cat.name.lower(), text.lower())
        if score > best_score:
            best_category, best_score = cat, score
    if best_category and best_score >= 0.5:
        return list(Product.objects.filter(category=best_category, active=True)[:5])
    return []


def _describe_order_delivery(order):
    if order.delivery_method_snapshot == "count" and order.delivery_rule_label_snapshot:
        return (
            f"Order {order.order_number} contains {order.delivery_quantity_snapshot} items. "
            f"Delivery is calculated using the Product Count Based method. "
            f"The applicable {order.delivery_rule_label_snapshot} delivery rule is ₹{order.delivery_charge}."
        )
    if order.delivery_method_snapshot == "weight" and order.delivery_rule_label_snapshot:
        return (
            f"Order {order.order_number} has a total shipment weight of {order.total_weight} kg. "
            f"Delivery is calculated using the Weight Based method. "
            f"The applicable {order.delivery_rule_label_snapshot} slab is ₹{order.delivery_charge}."
        )
    return f"Order {order.order_number} has a delivery charge of ₹{order.delivery_charge}."


def _authorized_order_answer(request, text):
    if not request.user.is_authenticated:
        return None
    from orders.models import Order
    import re
    qs = Order.objects.filter(user=request.user).order_by("-created_date")
    lower = text.lower()
    if "my orders" in lower or lower.strip() in {"orders", "my order history"}:
        recent = list(qs[:5])
        if not recent:
            return "You do not have any orders yet."
        lines = [f"{o.order_number} — {o.get_order_status_display()} — ₹{o.grand_total}" for o in recent]
        return "Your recent orders:\n" + "\n".join(lines)
    if any(k in lower for k in ["latest order", "recent order", "last order"]):
        order = qs.first()
        if not order:
            return "You do not have any orders yet."
        return f"Your latest order is {order.order_number}. Status: {order.get_order_status_display()}. Total: ₹{order.grand_total}."
    if "track" in lower or "order status" in lower or "where is my order" in lower or "shipped" in lower:
        order_number_match = re.search(r"DG\d{4,}", text.upper())
        order = qs.filter(order_number=order_number_match.group()).first() if order_number_match else qs.first()
        if not order:
            return "You do not have any orders yet." if not order_number_match else "I couldn't find that order on your account."
        return f"Order {order.order_number} is currently {order.get_order_status_display()}. Payment: {order.get_payment_status_display()}."
    if any(k in lower for k in ["delivery charge", "how much is delivery", "how is my delivery", "delivery calculated", "why is delivery", "delivery cost"]):
        order_number_match = re.search(r"DG\d{4,}", text.upper())
        if order_number_match:
            order = qs.filter(order_number=order_number_match.group()).first()
            if order:
                return _describe_order_delivery(order)
            return "I couldn't find that order on your account."
        order = qs.first()
        if order:
            return _describe_order_delivery(order)
        from orders.services.delivery import calculate_total_delivery
        from orders.services.checkout import get_checkout_lines
        lines = get_checkout_lines(request)
        if not lines:
            return "Delivery is calculated from the active admin delivery rules when you have items in checkout."
        return f"The current delivery charge for your selected items is ₹{calculate_total_delivery([(x['product'], x['quantity']) for x in lines])}."
    return None


@require_POST
def send_message(request):
    conv = _get_conversation(request)
    text = request.POST.get("text", "").strip()
    upload = request.FILES.get("attachment") or request.FILES.get("reference_image")

    attachment_type = ""
    if upload:
        content_type = (getattr(upload, "content_type", "") or "").lower()
        name = (upload.name or "").lower()
        size = getattr(upload, "size", 0)
        max_size = 25 * 1024 * 1024
        if size > max_size:
            return JsonResponse({"error": "Attachment must be 25 MB or smaller."}, status=400)

        if content_type.startswith("image/") or name.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            attachment_type = "image"
        elif content_type.startswith("video/") or name.endswith((".mp4", ".webm", ".mov", ".m4v")):
            attachment_type = "video"
        else:
            attachment_type = "file"

        allowed = {
            ".jpg", ".jpeg", ".png", ".webp", ".gif",
            ".mp4", ".webm", ".mov", ".m4v",
            ".pdf", ".txt", ".doc", ".docx", ".zip"
        }
        if not any(name.endswith(ext) for ext in allowed):
            return JsonResponse({"error": "This attachment type is not supported."}, status=400)

    msg = ChatMessage.objects.create(
        conversation=conv,
        sender="user",
        text=text,
        attachment=upload if upload else None,
        attachment_type=attachment_type,
        original_filename=getattr(upload, "name", "") if upload else "",
    )

    greeting_answer = intents.try_greeting(request, text) if text and not upload else None
    order_colour_answer = intents.try_order_colour(request, text) if text and not upload and not greeting_answer else None
    order_answer = _authorized_order_answer(request, text) if text and not upload and not order_colour_answer and not greeting_answer else None
    cart_answer = intents.try_my_cart(request, text) if text and not upload and not any([greeting_answer, order_colour_answer, order_answer]) else None
    details_answer = intents.try_my_details(request, text) if text and not upload and not any([greeting_answer, order_colour_answer, order_answer, cart_answer]) else None
    offers_answer = intents.try_offers(text) if text and not upload and not any([greeting_answer, order_colour_answer, order_answer, cart_answer, details_answer]) else None
    categories_answer = intents.try_show_categories(text) if text and not upload and not any([greeting_answer, order_colour_answer, order_answer, cart_answer, details_answer, offers_answer]) else None
    customize_answer = intents.try_customize(text) if text and not upload and not any([greeting_answer, order_colour_answer, order_answer, cart_answer, details_answer, offers_answer, categories_answer]) else None

    plain_text_answer = greeting_answer or order_colour_answer or order_answer or cart_answer or details_answer or offers_answer or categories_answer or customize_answer

    matches = []  # list of {"product": Product, "colour": Colour|None}
    if plain_text_answer:
        reply_text = plain_text_answer
    elif upload and not text:
        reply_text = "Thanks — I received your attachment. Tell me what you would like help with."
    else:
        result = (
            intents.try_product_colour_availability(text)
            or intents.try_show_specific_colour(text)
            or intents.try_colour_or_filtered_search(text)
        )
        if result:
            reply_text, matches = result
        else:
            legacy_matches = _find_matching_products(text)
            matches = [{"product": p, "colour": None} for p in legacy_matches]
            if matches:
                reply_text = "Here's what I found that might match:"
            else:
                reply_text = (
                    "I couldn't find an exact match — try a product name or category, "
                    "e.g. 'do you have wooden photo frames?'"
                )

    bot_msg = ChatMessage.objects.create(conversation=conv, sender="bot", text=reply_text)

    def _match_price(m):
        if m.get("colour"):
            v = m["product"].get_variant_by_colour_slug(m["colour"].name)
            if v:
                return v.effective_price
        return m["product"].effective_price

    return JsonResponse({
        "reply": reply_text,
        "products": [
            {
                "name": m["product"].name,
                "slug": m["product"].slug,
                "price": str(_match_price(m)),
                "colour": m["colour"].name if m.get("colour") else None,
                "colour_hex": m["colour"].hex_code if m.get("colour") else None,
                "url": intents.product_url(m["product"], m["colour"].name if m.get("colour") else None),
            }
            for m in matches
        ],
        "message": {
            "id": msg.id,
            "attachment_url": msg.attachment_url,
            "attachment_type": msg.attachment_type,
            "attachment_name": msg.attachment_name,
        },
    })
