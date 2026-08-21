"""Helpers to build the checkout context from either the cart or a buy-now session."""
from decimal import Decimal
from products.models import Product, ProductVariant
from .delivery import calculate_total_delivery, calculate_total_weight, calculate_slab_delivery, calculate_count_delivery, calculate_total_items


def get_checkout_lines(request):
    """
    Returns list of dicts: product, variant, quantity, customization_id, line_total, unit_price.
    Prefers a 'buy_now' session (Direct Checkout) over the cart.
    """
    buy_now = request.session.get("buy_now")
    if buy_now:
        try:
            product = Product.objects.get(id=buy_now["product_id"], active=True)
        except Product.DoesNotExist:
            return []
        variant = None
        variant_id = buy_now.get("variant_id")
        if variant_id:
            variant = ProductVariant.objects.filter(id=variant_id, product=product, active=True).select_related("colour").first()
            if not variant:
                return []  # variant was removed/disabled since buy-now started
        qty = buy_now["quantity"]
        unit_price = variant.effective_price if variant else product.effective_price
        return [{
            "product": product,
            "variant": variant,
            "quantity": qty,
            "customization_id": buy_now.get("customization_id"),
            "line_total": unit_price * qty,
            "unit_price": unit_price,
        }]
    from cart.cart import Cart
    return Cart(request).get_lines()


def is_direct_checkout(request):
    return bool(request.session.get("buy_now"))


def personalization_satisfied(customization):
    """A customization counts as complete only once the customer has done at
    least one of: uploaded a reference image, OR opted into WhatsApp
    checkout. Neither of those being true means personalization was never
    actually completed, regardless of what row exists in the DB."""
    if not customization:
        return False
    if customization.via_whatsapp:
        return True
    return customization.images.exists() or bool(customization.reference_image)


def unsatisfied_personalization_line(request):
    """Returns the first checkout line (cart or buy-now) whose product
    requires customization but doesn't have a completed personalization yet,
    or None if every customizable line is fine. Used to gate every entry
    point into checkout — the checkout pages themselves and place_order —
    so this can't be bypassed by opening a checkout URL directly."""
    from customization.models import Customization
    for line in get_checkout_lines(request):
        product = line["product"]
        if not product.customizable:
            continue
        customization = None
        if line.get("customization_id"):
            customization = Customization.objects.filter(id=line["customization_id"]).first()
        if not personalization_satisfied(customization):
            return line
    return None


def build_summary(request, coupon=None):
    lines = get_checkout_lines(request)
    subtotal = sum((l["line_total"] for l in lines), Decimal("0.00"))
    delivery_lines = [(l["product"], l["quantity"]) for l in lines]
    checkout_address = request.session.get("checkout_address") or {}
    state = checkout_address.get("state")
    delivery = calculate_total_delivery(delivery_lines, state=state)
    total_weight = calculate_total_weight(delivery_lines)
    _, _, delivery_slab = calculate_slab_delivery(delivery_lines) if delivery_lines else (Decimal("0.00"), Decimal("0.000"), None)
    _, _, delivery_rule = calculate_count_delivery(delivery_lines) if delivery_lines else (Decimal("0.00"), 0, None)
    discount = coupon.calculate_discount(subtotal) if coupon else Decimal("0.00")
    grand_total = subtotal - discount + delivery
    return {
        "lines": lines, "subtotal": subtotal, "discount": discount,
        "delivery": delivery, "grand_total": grand_total, "total_weight": total_weight, "delivery_slab": delivery_slab, "delivery_rule": delivery_rule, "total_items": calculate_total_items(delivery_lines),
        "delivery_state": state,
    }
