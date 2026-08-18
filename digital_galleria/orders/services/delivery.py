"""Single authoritative delivery calculation service."""
from decimal import Decimal
from orders.models import DeliveryWeightSlab, DeliveryCountRule
from site_settings.models import SiteSettings


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
    slab = None
    for candidate in DeliveryWeightSlab.objects.filter(is_active=True).order_by("priority", "min_weight", "id"):
        if weight >= candidate.min_weight and (candidate.max_weight is None or weight < candidate.max_weight):
            slab = candidate
            break
    return (slab.charge if slab else Decimal("0.00")), weight, slab


def calculate_count_delivery(lines):
    count = calculate_total_items(lines)
    rule = None
    for candidate in DeliveryCountRule.objects.filter(is_active=True).order_by("priority", "min_items", "id"):
        if count >= candidate.min_items and (candidate.max_items is None or count <= candidate.max_items):
            rule = candidate
            break
    return (rule.charge if rule else Decimal("0.00")), count, rule


class DeliveryConfigurationError(Exception):
    """Raised when the administrator has not configured the selected delivery mode."""


def delivery_is_configured():
    mode = SiteSettings.load().delivery_mode
    return DeliveryCountRule.objects.filter(is_active=True).exists() if mode == "count" else DeliveryWeightSlab.objects.filter(is_active=True).exists()


def calculate_total_delivery(lines):
    lines = list(lines)
    mode = SiteSettings.load().delivery_mode
    if mode == "count":
        if not DeliveryCountRule.objects.filter(is_active=True).exists():
            raise DeliveryConfigurationError("Product-count delivery rules are not configured by the administrator.")
        charge, _, _ = calculate_count_delivery(lines)
        return charge
    if not DeliveryWeightSlab.objects.filter(is_active=True).exists():
        raise DeliveryConfigurationError("Weight-based delivery slabs are not configured by the administrator.")
    charge, _, _ = calculate_slab_delivery(lines)
    return charge
