from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Address
from coupons.models import Coupon, CouponUsage
from customization.models import Customization
from site_settings.models import AssetSetting, SiteSettings

from .models import Order, OrderItem
from .services.checkout import build_summary, get_checkout_lines, is_direct_checkout
from .services.delivery import DeliveryConfigurationError, calculate_line_delivery, delivery_is_configured


def _get_applied_coupon(request):
    code = request.session.get("applied_coupon")
    if not code:
        return None
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return None
    return coupon if coupon.is_currently_valid() else None


def _address_snapshot(address):
    return {
        "full_name": address.full_name,
        "phone": address.phone,
        "house": address.house_building,
        "street": address.street,
        "area": address.area,
        "city": address.city,
        "district": address.district,
        "state": address.state,
        "pincode": address.pincode,
        "landmark": address.landmark,
    }


def _format_address(data):
    return (
        f"{data.get('full_name', '')}, {data.get('phone', '')}\n"
        f"{data.get('house', '')}, {data.get('street', '')}, {data.get('area', '')}\n"
        f"{data.get('city', '')}, {data.get('district', '')}, {data.get('state', '')} - {data.get('pincode', '')}\n"
        f"Landmark: {data.get('landmark', '')}"
    )


@login_required
def checkout_view(request):
    return redirect("orders:checkout_step1")


@login_required
def checkout_step1(request):
    lines = get_checkout_lines(request)
    if not lines:
        messages.info(request, "Your cart is empty.")
        return redirect("products:list")

    addresses = request.user.addresses.all().order_by("-is_default", "-created_date")
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    if request.method == "POST":
        if request.POST.get("use_alternate") == "on":
            required = ["alt_full_name", "alt_phone", "alt_house", "alt_street", "alt_city", "alt_state", "alt_pincode"]
            if any(not request.POST.get(key, "").strip() for key in required):
                messages.error(request, "Please complete the required delivery address fields.")
            else:
                data = {
                    "full_name": request.POST.get("alt_full_name", "").strip(),
                    "phone": request.POST.get("alt_phone", "").strip(),
                    "house": request.POST.get("alt_house", "").strip(),
                    "street": request.POST.get("alt_street", "").strip(),
                    "area": request.POST.get("alt_area", "").strip(),
                    "city": request.POST.get("alt_city", "").strip(),
                    "district": request.POST.get("alt_district", "").strip(),
                    "state": request.POST.get("alt_state", "").strip(),
                    "pincode": request.POST.get("alt_pincode", "").strip(),
                    "landmark": request.POST.get("alt_landmark", "").strip(),
                }
                request.session["checkout_address"] = data
                if request.POST.get("save_as_default"):
                    Address.objects.create(user=request.user, full_name=data["full_name"], phone=data["phone"], house_building=data["house"], street=data["street"], area=data["area"], city=data["city"], district=data["district"], state=data["state"], pincode=data["pincode"], landmark=data["landmark"], is_default=True)
                return redirect("orders:checkout_step2")
        else:
            address = Address.objects.filter(id=request.POST.get("address_id"), user=request.user).first()
            if address:
                request.session["checkout_address"] = _address_snapshot(address)
                return redirect("orders:checkout_step2")
            messages.error(request, "Please select a delivery address or choose a different address.")

    return render(request, "checkout/step1.html", {
        "addresses": addresses,
        "default_address": default_address,
        "is_direct_checkout": is_direct_checkout(request),
    })


@login_required
def checkout_step2(request):
    lines = get_checkout_lines(request)
    if not lines:
        return redirect("products:list")
    if not request.session.get("checkout_address"):
        return redirect("orders:checkout_step1")
    if not delivery_is_configured():
        messages.error(request, "Checkout is temporarily unavailable because delivery rules are not configured by the administrator.")
        return redirect("orders:checkout_step1")
    if not SiteSettings.load().payment_available:
        messages.error(request, "Online payment is currently unavailable. Please contact the store administrator.")
        return redirect("orders:checkout_step1")
    coupon = _get_applied_coupon(request)
    try:
        summary = build_summary(request, coupon=coupon)
    except DeliveryConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("orders:checkout_step1")
    return render(request, "checkout/step2.html", {
        "summary": summary,
        "applied_coupon": coupon,
        "is_direct_checkout": is_direct_checkout(request),
        "delivery_mode": SiteSettings.load().delivery_mode,
    })


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip()
    if request.POST.get("remove"):
        request.session.pop("applied_coupon", None)
        messages.info(request, "Coupon removed.")
        return redirect("orders:checkout_step2")
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code.")
        return redirect("orders:checkout_step2")
    if not coupon.is_currently_valid():
        messages.error(request, "This coupon is not currently active.")
        return redirect("orders:checkout_step2")
    if coupon.usage_limit and coupon.usage_count() >= coupon.usage_limit:
        messages.error(request, "This coupon has reached its usage limit.")
        return redirect("orders:checkout_step2")
    if coupon.user_usage_count(request.user) >= coupon.per_user_limit:
        messages.error(request, "You have already used this coupon.")
        return redirect("orders:checkout_step2")
    try:
        summary = build_summary(request)
    except DeliveryConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("orders:checkout_step1")
    if summary["subtotal"] < coupon.minimum_order:
        messages.error(request, f"Minimum order of ₹{coupon.minimum_order} required for this coupon.")
        return redirect("orders:checkout_step2")
    request.session["applied_coupon"] = coupon.code
    messages.success(request, f"Coupon '{coupon.code}' applied.")
    return redirect("orders:checkout_step2")


@login_required
@require_POST
def place_order(request):
    lines = get_checkout_lines(request)
    if not lines:
        messages.error(request, "Nothing to order.")
        return redirect("products:list")
    address_data = request.session.get("checkout_address")
    if not address_data:
        messages.error(request, "Please complete delivery details first.")
        return redirect("orders:checkout_step1")
    if not delivery_is_configured():
        messages.error(request, "Checkout is temporarily unavailable because delivery rules are not configured by the administrator.")
        return redirect("orders:checkout_step1")
    if not SiteSettings.load().payment_available:
        messages.error(request, "Online payment is currently unavailable. Please contact the store administrator.")
        return redirect("orders:checkout_step1")

    for line in lines:
        if line["quantity"] > line["product"].stock:
            messages.error(request, f"{line['product'].name} has insufficient stock.")
            return redirect("orders:checkout_step1")

    coupon = _get_applied_coupon(request)
    try:
        summary = build_summary(request, coupon=coupon)
    except DeliveryConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("orders:checkout_step1")

    with transaction.atomic():
        delivery_mode = SiteSettings.load().delivery_mode
        if delivery_mode == "count":
            rule = summary.get("delivery_rule")
            delivery_rule_label = (f"{rule.min_items}{'–' + str(rule.max_items) if rule.max_items else '+'} items") if rule else ""
            delivery_quantity = summary["total_items"]
        else:
            slab = summary.get("delivery_slab")
            delivery_rule_label = (f"{slab.min_weight}–{slab.max_weight if slab.max_weight else 'open'}kg") if slab else ""
            delivery_quantity = summary["total_items"]
        order = Order.objects.create(
            user=request.user,
            customer_name_snapshot=address_data["full_name"],
            phone_snapshot=address_data["phone"],
            email_snapshot=request.user.email,
            delivery_address_snapshot=_format_address(address_data),
            subtotal=summary["subtotal"],
            discount=summary["discount"],
            delivery_charge=summary["delivery"],
            total_weight=summary["total_weight"],
            grand_total=summary["grand_total"],
            coupon=coupon,
            expected_delivery_date=timezone.now().date() + timezone.timedelta(days=5),
            delivery_method_snapshot=delivery_mode,
            delivery_quantity_snapshot=delivery_quantity,
            delivery_rule_label_snapshot=delivery_rule_label,
        )
        for line in lines:
            product = line["product"]
            qty = line["quantity"]
            product.refresh_from_db()
            if qty > product.stock:
                raise ValueError(f"Insufficient stock for {product.name}")
            product.stock -= qty
            product.save(update_fields=["stock"])
            customization = None
            if line.get("customization_id"):
                customization = Customization.objects.filter(id=line["customization_id"], user=request.user).first()
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name_snapshot=product.name,
                price_snapshot=product.effective_price,
                quantity=qty,
                subtotal=line["line_total"],
                delivery_snapshot=calculate_line_delivery(product, qty),
                customization=customization,
            )
            if customization and customization.via_whatsapp:
                settings_obj = SiteSettings.load()
                if settings_obj.whatsapp_include_order_number:
                    message = customization.whatsapp_message or settings_obj.whatsapp_default_message
                    message += f"\nOrder: {order.order_number}"
                    customization.whatsapp_message = message
                    customization.save(update_fields=["whatsapp_message"])
        if coupon:
            CouponUsage.objects.create(coupon=coupon, user=request.user, order=order)

    if is_direct_checkout(request):
        request.session.pop("buy_now", None)
    else:
        from cart.cart import Cart
        Cart(request).clear()
    request.session.pop("applied_coupon", None)
    request.session.pop("checkout_address", None)

    from payments.models import Payment
    Payment.objects.get_or_create(order=order)
    return redirect("payments:pay", order_number=order.order_number)


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/detail.html", {"order": order})


@login_required
@require_POST
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    settings_obj = SiteSettings.load()
    statuses = ["verified", "processing", "shipped", "delivered"]
    cutoff = statuses.index(settings_obj.cancellation_cutoff_status)
    current = statuses.index(order.order_status) if order.order_status in statuses else len(statuses)
    if order.order_status == "cancelled" or current > cutoff:
        messages.error(request, "This order can no longer be cancelled.")
        return redirect("orders:tracking", order_number=order.order_number)
    order.order_status = "cancelled"
    order.refund_status = "pending" if order.payment_status == "received" else "none"
    order.cancellation_reason = request.POST.get("reason", "Customer requested cancellation")
    order.save(update_fields=["order_status", "refund_status", "cancellation_reason", "updated_date"])
    messages.success(request, "Order cancelled successfully.")
    return redirect("orders:tracking", order_number=order.order_number)


@login_required
def tracking_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    settings_obj = SiteSettings.load()
    statuses = ["verified", "processing", "shipped", "delivered"]
    can_cancel = order.order_status in statuses and statuses.index(order.order_status) <= statuses.index(settings_obj.cancellation_cutoff_status)
    return render(request, "orders/tracking.html", {
        "order": order,
        "vehicle": request.user.preferred_vehicle,
        "can_cancel": can_cancel,
        "tracking_asset": (
            AssetSetting.objects.filter(
                key=("delivery_scooter" if request.user.preferred_vehicle == "scooter" else "delivery_bike"),
                enabled=True,
            ).first()
            or AssetSetting.objects.filter(key="delivery_bike", enabled=True).first()
        ),
        "refund_asset": AssetSetting.objects.filter(key="refund", enabled=True).first(),
    })
