"""Order-triggered stock changes — deliberately NOT called at order
placement or payment-confirmation time. Stock is only decremented once an
order actually reaches "Processing" (or a later stage), and is restored if
a since-processed order is later cancelled. Called exclusively from
Order.save() (see orders/models.py) so every path that changes
order_status behaves the same way, with no duplicate logic elsewhere."""
from django.db import transaction

from orders.models import Order


def deduct_stock_for_order(order):
    """Decrement product/variant stock for every item on this order. Safe to
    call only once per order — the caller (Order.save()) checks
    stock_deducted before calling this."""
    from products.models import Product, ProductVariant

    with transaction.atomic():
        for item in order.items.select_related("product", "variant"):
            qty = item.quantity
            if item.variant_id:
                variant = ProductVariant.objects.select_for_update().filter(pk=item.variant_id).first()
                if variant:
                    variant.stock = max(0, variant.stock - qty)
                    variant.save(update_fields=["stock"])
            elif item.product_id:
                product = Product.objects.select_for_update().filter(pk=item.product_id).first()
                if product:
                    product.stock = max(0, product.stock - qty)
                    product.save(update_fields=["stock"])
        Order.objects.filter(pk=order.pk).update(stock_deducted=True)
        order.stock_deducted = True


def restock_order(order):
    """Add back product/variant stock for every item on this order. Safe to
    call only for an order whose stock_deducted was True — the caller
    (Order.save()) checks that before calling this."""
    from products.models import Product, ProductVariant

    with transaction.atomic():
        for item in order.items.select_related("product", "variant"):
            qty = item.quantity
            if item.variant_id:
                variant = ProductVariant.objects.select_for_update().filter(pk=item.variant_id).first()
                if variant:
                    variant.stock = variant.stock + qty
                    variant.save(update_fields=["stock"])
            elif item.product_id:
                product = Product.objects.select_for_update().filter(pk=item.product_id).first()
                if product:
                    product.stock = product.stock + qty
                    product.save(update_fields=["stock"])
        Order.objects.filter(pk=order.pk).update(stock_deducted=False)
        order.stock_deducted = False
