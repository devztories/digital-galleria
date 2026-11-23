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


def calculate_line_delivery_for_product(product, quantity: int):
    """Resolves ONE cart/order line's delivery charge using THAT product's
    own delivery_pricing_mode (Admin → Products → this product), decided by
    the admin when the product was added. Returns None when the product is
    left on 'site_default', signalling the caller to fall back to whatever
    delivery mode is configured site-wide (Site Settings → Delivery) instead.
    A product with delivery disabled (or marked free delivery) never charges,
    no matter which pricing mode it's on.
    """
    if quantity <= 0 or not product.delivery_enabled or product.free_delivery:
        return Decimal("0.00")
    mode = getattr(product, "delivery_pricing_mode", "site_default")
    if mode == "product":
        return calculate_line_delivery(product, quantity)
    if mode == "count":
        charge, _, _ = calculate_count_delivery([(product, quantity)])
        return charge
    return None


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


def get_product_delivery_estimate(product, quantity, state=None):
    """Storefront-facing (product detail page) delivery estimate for a SINGLE
    product at a given quantity — independent of what's actually in the
    cart. Mirrors the per-line resolution used by calculate_total_delivery,
    but always returns a displayable result (never raises) so the product
    page can show 'Delivery charge unavailable' instead of a hard failure.

    Returns a dict:
      enabled     - False when the product has delivery disabled or is free
                    delivery (nothing further to show).
      needs_state - True when the charge depends on Kerala vs Outside Kerala,
                    so the storefront should render the toggle.
      charge      - Decimal charge for the given quantity/state, or None if
                    the relevant delivery rules aren't configured yet.
      unconfigured- True when 'charge' is None because of missing admin config.
    """
    quantity = max(1, int(quantity or 1))
    if not product.delivery_enabled or product.free_delivery:
        return {"enabled": False, "needs_state": False, "charge": Decimal("0.00"), "unconfigured": False}

    mode = getattr(product, "delivery_pricing_mode", "site_default")
    if mode == "product":
        return {"enabled": True, "needs_state": False, "charge": calculate_line_delivery(product, quantity), "unconfigured": False}
    if mode == "count":
        charge, _, _ = calculate_count_delivery([(product, quantity)])
        return {"enabled": True, "needs_state": False, "charge": charge, "unconfigured": False}

    site_mode = SiteSettings.load().delivery_mode
    if site_mode == "product_state":
        charge = calculate_line_state_delivery(product, quantity, state or "kerala")
        return {"enabled": True, "needs_state": True, "charge": charge, "unconfigured": False}
    if site_mode == "count":
        if not DeliveryCountRule.objects.filter(is_active=True).exists():
            return {"enabled": True, "needs_state": False, "charge": None, "unconfigured": True}
        charge, _, _ = calculate_count_delivery([(product, quantity)])
        return {"enabled": True, "needs_state": False, "charge": charge, "unconfigured": False}
    # weight
    if not DeliveryWeightSlab.objects.filter(is_active=True).exists():
        return {"enabled": True, "needs_state": False, "charge": None, "unconfigured": True}
    charge, _, _ = calculate_slab_delivery([(product, quantity)])
    return {"enabled": True, "needs_state": False, "charge": charge, "unconfigured": False}


class DeliveryConfigurationError(Exception):
    """Raised when the administrator has not configured the selected delivery mode."""


def delivery_is_configured():
    """Whether SOME delivery charge can be computed. Per-product 'Product Based'
    lines are always self-contained (their own fee fields). Per-product 'Count
    Based' lines need the site's Count Rules configured. 'site_default' lines
    fall back to whatever the site-wide mode is, which needs its own rules."""
    mode = SiteSettings.load().delivery_mode
    if mode == "product_state":
        # Configuration lives on each product (Admin → Products), not in a
        # separate rule table, so there's nothing global to require here.
        return True
    return DeliveryCountRule.objects.filter(is_active=True).exists() if mode == "count" else DeliveryWeightSlab.objects.filter(is_active=True).exists()


def calculate_total_delivery(lines, state=None):
    """Sums delivery charge per line. Each product decides its own pricing
    mode (Admin → Products → Delivery Pricing Mode), set when the product was
    added: 'Product Based' and 'Count Based' lines are resolved independently,
    right here, using that product's own settings. Any line left on
    'Use Site-wide Delivery Setting' is pooled together and resolved via
    whichever delivery mode is configured in Site Settings → Delivery, exactly
    as before this per-product option existed."""
    lines = list(lines)
    total = Decimal("0.00")
    site_default_lines = []
    for product, quantity in lines:
        if quantity <= 0:
            continue
        line_charge = calculate_line_delivery_for_product(product, quantity)
        if line_charge is None:
            site_default_lines.append((product, quantity))
        else:
            total += line_charge

    if not site_default_lines:
        return total

    mode = SiteSettings.load().delivery_mode
    if mode == "product_state":
        total += calculate_state_delivery(site_default_lines, state)
    elif mode == "count":
        if not DeliveryCountRule.objects.filter(is_active=True).exists():
            raise DeliveryConfigurationError("Product-count delivery rules are not configured by the administrator.")
        charge, _, _ = calculate_count_delivery(site_default_lines)
        total += charge
    else:
        if not DeliveryWeightSlab.objects.filter(is_active=True).exists():
            raise DeliveryConfigurationError("Weight-based delivery slabs are not configured by the administrator.")
        charge, _, _ = calculate_slab_delivery(site_default_lines)
        total += charge
    return total
