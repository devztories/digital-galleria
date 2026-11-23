"""Hooks that turn store events into admin notifications."""
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from .services import notify_admins


def _admin_url(name, *args):
    try:
        return reverse(name, args=args)
    except Exception:
        return "/admin/"


# --- Orders -----------------------------------------------------------------
@receiver(pre_save, sender="orders.Order")
def _remember_previous_order_state(sender, instance, **kwargs):
    instance._prev_state = None
    if instance.pk:
        instance._prev_state = sender.objects.filter(pk=instance.pk).values("order_status", "payment_status").first()


@receiver(post_save, sender="orders.Order")
def _order_events(sender, instance, created, **kwargs):
    prev = getattr(instance, "_prev_state", None)
    if created or not prev:
        return  # "awaiting_payment" rows aren't real orders yet — see Order.STATUS_CHOICES
    url = _admin_url("dg_admin:order_detail", instance.order_number)
    name = instance.customer_name_snapshot or "A customer"

    # Customer submitted payment proof -> the order becomes real ("verified").
    if prev["order_status"] == "awaiting_payment" and instance.order_status == "verified":
        notify_admins("order", f"New order {instance.order_number}",
                      f"{name} · ₹{instance.grand_total} · payment proof submitted, needs review", url)
    # Customer re-submitted proof after a rejection.
    elif prev["payment_status"] == "rejected" and instance.payment_status == "pending":
        notify_admins("payment", f"Payment re-submitted · {instance.order_number}",
                      f"{name} uploaded new payment proof for ₹{instance.grand_total}", url)
    # Customer cancelled.
    if prev["order_status"] != "cancelled" and instance.order_status == "cancelled":
        notify_admins("order", f"Order cancelled · {instance.order_number}",
                      f"{name} · ₹{instance.grand_total}" + (f" · {instance.cancellation_reason[:120]}" if instance.cancellation_reason else ""), url)


# --- Customizations ---------------------------------------------------------
@receiver(post_save, sender="customization.Customization")
def _customization_created(sender, instance, created, **kwargs):
    if not created:
        return
    via = "via WhatsApp" if instance.via_whatsapp else "on the website"
    notify_admins("customization", f"New customization · {instance.product.name}",
                  f"{instance.user.name or instance.user.email} is sending images {via}",
                  _admin_url("dg_admin:customization_list"))


# --- New customer -----------------------------------------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def _new_customer(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        notify_admins("customer", "New customer registered",
                      f"{instance.name or instance.email} · {instance.email}",
                      _admin_url("dg_admin:customer_detail", instance.pk))


# --- Low stock --------------------------------------------------------------
@receiver(pre_save, sender="products.Product")
def _remember_stock(sender, instance, **kwargs):
    instance._prev_stock = None
    if instance.pk:
        row = sender.objects.filter(pk=instance.pk).values("stock").first()
        instance._prev_stock = row["stock"] if row else None


@receiver(post_save, sender="products.Product")
def _low_stock(sender, instance, created, **kwargs):
    prev = getattr(instance, "_prev_stock", None)
    if created or prev is None:
        return
    threshold = getattr(settings, "LOW_STOCK_THRESHOLD", 5)
    if instance.stock <= threshold < prev:  # only fire when crossing the threshold
        label = "Out of stock" if instance.stock == 0 else "Low stock"
        notify_admins("stock", f"{label} · {instance.name}", f"Only {instance.stock} left (alert level {threshold})",
                      _admin_url("dg_admin:product_edit", instance.pk))
