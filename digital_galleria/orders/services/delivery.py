"""Single authoritative delivery calculation service."""
import math
from decimal import Decimal
from orders.models import DeliveryWeightSlab, DeliveryCountRule
from site_settings.models import SiteSettings

# Every value here, once trimmed and lowercased, is treated as Kerala —
# covers full-name/short-code and any case/whitespace variation.
KERALA_ALIASES = {"kerala", "kl"}


def normalize_state(state):
    """Trim whitespace and lowercase, so comparisons are case/space-insensitive."""
    return (state or "").strip().lower()


def is_kerala_state(state):
    return normalize_state(state) in KERALA_ALIASES


def _weight_in_kg(product):
    weight = product.weight or Decimal("0")
    if product.weight_unit == "g":
        return weight / Decimal("1000")
    return weight


def calculate_total_weight(lines):
    total = Decimal("0.000")
    for product, quantity in lines:
        if quantity <= 0:
            continue
        total += _weight_in_kg(product) * Decimal(quantity)
    return total.quantize(Decimal("0.001"))


def calculate_total_items(lines):
    return sum(max(0, int(quantity)) for _, quantity in lines)


def calculate_line_delivery(product, quantity: int) -> Decimal:
    if quantity <= 0 or not product.delivery_enabled or product.free_delivery:
        return Decimal("0.00")
    first = product.first_item_delivery_charge or Decimal("0.00")
    additional = product.additional_item_delivery_charge or Decimal("0.00")
    return first + (additional * (quantity - 1))


def calculate_slab_delivery(lines):
    weight = calculate_total_weight(lines)
    slabs = list(DeliveryWeightSlab.objects.filter(is_active=True).order_by("priority", "min_weight", "id"))
    slab = None
    for candidate in slabs:
        if weight >= candidate.min_weight and (candidate.max_weight is None or weight < candidate.max_weight):
            slab = candidate
            break
    if slab is None and slabs:
        # Weight fell outside every configured range — e.g. a product's
        # weight was never set (0kg) and the lowest slab starts above 0, or
        # there's a gap between two slabs. A delivery mode IS configured, so
        # never silently charge ₹0 here; use whichever configured slab is
        # closest to this weight instead (the next tier up if we're below
        # everything, otherwise the heaviest/catch-all tier).
        by_min = sorted(slabs, key=lambda s: s.min_weight)
        above_or_equal = [s for s in by_min if weight < s.min_weight]
        slab = above_or_equal[0] if above_or_equal else by_min[-1]
    return (slab.charge if slab else Decimal("0.00")), weight, slab


def calculate_count_delivery(lines):
    count = calculate_total_items(lines)
    rules = list(DeliveryCountRule.objects.filter(is_active=True).order_by("priority", "min_items", "id"))
    rule = None
    for candidate in rules:
        if count >= candidate.min_items and (candidate.max_items is None or count <= candidate.max_items):
            rule = candidate
            break
    if rule is None and rules:
        # Same gap-safety as calculate_slab_delivery: never silently drop
        # the delivery charge to ₹0 just because the item count doesn't
        # land exactly inside a configured range.
        by_min = sorted(rules, key=lambda r: r.min_items)
        above_or_equal = [r for r in by_min if count < r.min_items]
        rule = above_or_equal[0] if above_or_equal else by_min[-1]
    return (rule.charge if rule else Decimal("0.00")), count, rule


def calculate_line_state_delivery(product, quantity, state):
    """Per-product, quantity-stepped delivery charge based on whether the
    delivery address is inside or outside Kerala (state normalized/aliased —
    see is_kerala_state). Base charge covers the first item; the additional
    charge is applied once per `qty_step` items beyond the first (default
    step of 1 == once per extra item), e.g. base=50, additional=20, step=1
    gives qty1=50, qty2=70, qty3=90, qty4=110."""
    if quantity <= 0 or not product.delivery_enabled or product.free_delivery:
        return Decimal("0.00")
    if is_kerala_state(state):
        base = product.inside_kerala_delivery_charge or Decimal("0.00")
        step = product.inside_kerala_delivery_qty_step or 1
        additional = product.inside_kerala_delivery_additional_charge or Decimal("0.00")
    else:
        base = product.outside_kerala_delivery_charge or Decimal("0.00")
        step = product.outside_kerala_delivery_qty_step or 1
        additional = product.outside_kerala_delivery_additional_charge or Decimal("0.00")
    if quantity <= 1:
        return base
    step = step or 1
    extra_units = math.ceil((quantity - 1) / step)
    return base + (additional * extra_units)


def calculate_state_delivery(lines, state):
    total = Decimal("0.00")
    for product, quantity in lines:
        if quantity <= 0:
            continue
        total += calculate_line_state_delivery(product, quantity, state)
    return total


class DeliveryConfigurationError(Exception):
    """Raised when the administrator has not configured the selected delivery mode."""


def delivery_is_configured():
    mode = SiteSettings.load().delivery_mode
    if mode == "product_state":
        # Configuration lives on each product (Admin → Products), not in a
        # separate rule table, so there's nothing global to require here.
        return True
    return DeliveryCountRule.objects.filter(is_active=True).exists() if mode == "count" else DeliveryWeightSlab.objects.filter(is_active=True).exists()


def calculate_total_delivery(lines, state=None):
    lines = list(lines)
    mode = SiteSettings.load().delivery_mode
    if mode == "product_state":
        return calculate_state_delivery(lines, state)
    if mode == "count":
        if not DeliveryCountRule.objects.filter(is_active=True).exists():
            raise DeliveryConfigurationError("Product-count delivery rules are not configured by the administrator.")
        charge, _, _ = calculate_count_delivery(lines)
        return charge
    if not DeliveryWeightSlab.objects.filter(is_active=True).exists():
        raise DeliveryConfigurationError("Weight-based delivery slabs are not configured by the administrator.")
    charge, _, _ = calculate_slab_delivery(lines)
    return charge
