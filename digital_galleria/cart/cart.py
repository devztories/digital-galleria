"""
Session-based shopping cart.

Structure stored in session:
    {"<product_id>:<variant_id_or_0>": {"quantity": int, "customization_id": int|None, "variant_id": int|None}}

Using "product_id:variant_id" as the key (instead of just product_id) means
the SAME product in two different colours becomes two separate cart line
items — they are never merged. variant_id is "0" when the product has no
colour variants (legacy / non-variant products). get_lines() also still
understands the old bare-product_id key format for carts saved before the
variant system existed.
"""
from decimal import Decimal
from products.models import Product, ProductVariant
from site_settings.models import SiteSettings
from orders.services.delivery import calculate_total_delivery, calculate_total_weight, calculate_slab_delivery, calculate_count_delivery, calculate_total_items, delivery_is_configured, DeliveryConfigurationError

SESSION_KEY = "cart"


def _make_key(product_id, variant_id=None):
    return f"{product_id}:{variant_id or 0}"


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

    def add(self, product, quantity=1, customization_id=None, variant_id=None):
        key = _make_key(product.id, variant_id)
        if key in self.cart:
            self.cart[key]["quantity"] += quantity
        else:
            self.cart[key] = {"quantity": quantity, "customization_id": customization_id, "variant_id": variant_id}
        self.save()

    def _find_key(self, product_id, variant_id=None):
        key = _make_key(product_id, variant_id)
        if key in self.cart:
            return key
        legacy_key = str(product_id)
        if not variant_id and legacy_key in self.cart:
            return legacy_key
        return None

    def set_quantity(self, product_id, quantity, variant_id=None):
        key = self._find_key(product_id, variant_id)
        if key:
            if quantity <= 0:
                del self.cart[key]
            else:
                self.cart[key]["quantity"] = quantity
            self.save()

    def remove(self, product_id, variant_id=None):
        key = self._find_key(product_id, variant_id)
        if key:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[SESSION_KEY] = {}
        self.save()

    def set_customization(self, cart_key, customization_id):
        """Attaches a Customization to one specific cart line (product+variant),
        never to other lines of the same product in a different colour."""
        if cart_key in self.cart:
            self.cart[cart_key]["customization_id"] = customization_id
            self.save()

    def get_line(self, cart_key):
        return next((l for l in self.get_lines() if l["cart_key"] == cart_key), None)

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_lines(self):
        """Returns list of dicts with product, variant, quantity, customization, line_total.
        Each (product, variant) pair is its own independent line — same product
        in two different colours never merges."""
        lines = []
        product_ids = set()
        variant_ids = set()
        for key in self.cart.keys():
            pid_str, sep, vid_str = key.partition(":")
            product_ids.add(int(pid_str))
            if sep and vid_str and vid_str != "0":
                variant_ids.add(int(vid_str))

        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related("colour")
        variant_map = {v.id: v for v in variants}

        for key, data in self.cart.items():
            pid_str, sep, vid_str = key.partition(":")
            product = product_map.get(int(pid_str))
            if not product:
                continue
            variant = None
            if sep and vid_str and vid_str != "0":
                variant = variant_map.get(int(vid_str))
                if not variant:
                    # Variant was deleted by admin since being added — skip the stale line.
                    continue
            qty = data["quantity"]
            unit_price = variant.effective_price if variant else product.effective_price
            lines.append({
                "cart_key": key,
                "product": product,
                "variant": variant,
                "quantity": qty,
                "customization_id": data.get("customization_id"),
                "line_total": unit_price * qty,
                "unit_price": unit_price,
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
