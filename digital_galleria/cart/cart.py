"""
Session-based shopping cart.
Structure stored in session: {"<product_id>": {"quantity": int, "customization_id": int|None}}
"""
from decimal import Decimal
from products.models import Product
from site_settings.models import SiteSettings
from orders.services.delivery import calculate_total_delivery, calculate_total_weight, calculate_slab_delivery, calculate_count_delivery, calculate_total_items, delivery_is_configured, DeliveryConfigurationError

SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[SESSION_KEY] = cart
        self.cart = cart

    def save(self):
        self.session[SESSION_KEY] = self.cart
        self.session.modified = True

    def add(self, product, quantity=1, customization_id=None):
        pid = str(product.id)
        if pid in self.cart:
            self.cart[pid]["quantity"] += quantity
        else:
            self.cart[pid] = {"quantity": quantity, "customization_id": customization_id}
        self.save()

    def set_quantity(self, product_id, quantity):
        pid = str(product_id)
        if pid in self.cart:
            if quantity <= 0:
                del self.cart[pid]
            else:
                self.cart[pid]["quantity"] = quantity
            self.save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session[SESSION_KEY] = {}
        self.save()

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_lines(self):
        """Returns list of dicts with product, quantity, customization, line_total."""
        lines = []
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}
        for pid, data in self.cart.items():
            product = product_map.get(int(pid))
            if not product:
                continue
            qty = data["quantity"]
            lines.append({
                "product": product,
                "quantity": qty,
                "customization_id": data.get("customization_id"),
                "line_total": product.effective_price * qty,
            })
        return lines

    def summary(self, coupon=None):
        lines = self.get_lines()
        subtotal = sum((l["line_total"] for l in lines), Decimal("0.00"))
        delivery_lines = [(l["product"], l["quantity"]) for l in lines]
        configured = delivery_is_configured()
        try:
            delivery = calculate_total_delivery(delivery_lines) if delivery_lines else Decimal("0.00")
        except DeliveryConfigurationError:
            delivery = Decimal("0.00")
        total_weight = calculate_total_weight(delivery_lines)
        _, _, delivery_slab = calculate_slab_delivery(delivery_lines) if delivery_lines else (Decimal("0.00"), Decimal("0.000"), None)
        _, _, delivery_rule = calculate_count_delivery(delivery_lines) if delivery_lines and configured and SiteSettings.load().delivery_mode == "count" else (Decimal("0.00"), 0, None)
        discount = coupon.calculate_discount(subtotal) if coupon else Decimal("0.00")
        grand_total = subtotal - discount + delivery
        return {
            "lines": lines,
            "subtotal": subtotal,
            "discount": discount,
            "delivery": delivery,
            "grand_total": grand_total,
            "total_weight": total_weight,
            "delivery_slab": delivery_slab,
            "delivery_rule": delivery_rule, "delivery_configured": configured,
            "total_items": calculate_total_items(delivery_lines),
        }
