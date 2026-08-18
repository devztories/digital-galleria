"""Helpers to build the checkout context from either the cart or a buy-now session."""
from decimal import Decimal
from products.models import Product
from .delivery import calculate_total_delivery, calculate_total_weight, calculate_slab_delivery, calculate_count_delivery, calculate_total_items


def get_checkout_lines(request):
    """
    Returns list of dicts: product, quantity, customization_id, line_total.
    Prefers a 'buy_now' session (Direct Checkout) over the cart.
    """
    buy_now = request.session.get("buy_now")
    if buy_now:
        try:
            product = Product.objects.get(id=buy_now["product_id"], active=True)
        except Product.DoesNotExist:
            return []
        qty = buy_now["quantity"]
        return [{
            "product": product,
            "quantity": qty,
            "customization_id": buy_now.get("customization_id"),
            "line_total": product.effective_price * qty,
        }]
    from cart.cart import Cart
    return Cart(request).get_lines()


def is_direct_checkout(request):
    return bool(request.session.get("buy_now"))


def build_summary(request, coupon=None):
    lines = get_checkout_lines(request)
    subtotal = sum((l["line_total"] for l in lines), Decimal("0.00"))
    delivery_lines = [(l["product"], l["quantity"]) for l in lines]
    delivery = calculate_total_delivery(delivery_lines)
    total_weight = calculate_total_weight(delivery_lines)
    _, _, delivery_slab = calculate_slab_delivery(delivery_lines) if delivery_lines else (Decimal("0.00"), Decimal("0.000"), None)
    _, _, delivery_rule = calculate_count_delivery(delivery_lines) if delivery_lines else (Decimal("0.00"), 0, None)
    discount = coupon.calculate_discount(subtotal) if coupon else Decimal("0.00")
    grand_total = subtotal - discount + delivery
    return {
        "lines": lines, "subtotal": subtotal, "discount": discount,
        "delivery": delivery, "grand_total": grand_total, "total_weight": total_weight, "delivery_slab": delivery_slab, "delivery_rule": delivery_rule, "total_items": calculate_total_items(delivery_lines),
    }
