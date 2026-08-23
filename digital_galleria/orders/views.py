from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Address, INDIAN_STATE_CHOICES
from coupons.models import Coupon, CouponUsage
from customization.models import Customization
from site_settings.models import AssetSetting, SiteSettings

from .models import Order, OrderItem
from .services.checkout import build_summary, get_checkout_lines, is_direct_checkout, unsatisfied_personalization_line
from .services.delivery import DeliveryConfigurationError, calculate_line_delivery, calculate_line_state_delivery, delivery_is_configured, is_kerala_state


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


def _redirect_to_personalize(request, line):
    """Sends the customer to complete personalization for the given
    checkout line instead of letting checkout continue."""
    from django.urls import reverse
    product = line["product"]
    messages.error(request, f"Please upload an image or enable WhatsApp checkout for \"{product.name}\" before continuing.")
    if is_direct_checkout(request):
        url = reverse("customization:customize", args=[product.slug])
        variant = line.get("variant")
        if variant:
            url += f"?variant_id={variant.id}"
        return redirect(url)
    cart_key = line.get("cart_key")
    if cart_key:
        return redirect("customization:customize_cart_item", cart_key=cart_key)
    return redirect("cart:cart")


@login_required
def checkout_step1(request):
    lines = get_checkout_lines(request)
    if not lines:
        messages.info(request, "Your cart is empty.")
        return redirect("products:list")

    # Personalization must be completed (image OR WhatsApp) before a
    # customizable product can proceed to checkout — enforced here so this
    # applies whether the customer arrived via Buy Now or Proceed to
    # Checkout, and can't be skipped by opening this URL directly.
    unsatisfied = unsatisfied_personalization_line(request)
    if unsatisfied:
        return _redirect_to_personalize(request, unsatisfied)

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
                request.session.pop("checkout_delivery_state_override", None)
                if request.POST.get("save_as_default"):
                    existing = Address.find_duplicate(request.user, data)
                    if existing:
                        existing.full_name = data["full_name"]
                        existing.phone = data["phone"]
                        existing.house_building = data["house"]
                        existing.street = data["street"]
                        existing.area = data["area"]
                        existing.city = data["city"]
                        existing.district = data["district"]
                        existing.state = data["state"]
                        existing.pincode = data["pincode"]
                        existing.landmark = data["landmark"]
                        existing.is_default = True
                        existing.save()
                    else:
                        Address.objects.create(user=request.user, full_name=data["full_name"], phone=data["phone"], house_building=data["house"], street=data["street"], area=data["area"], city=data["city"], district=data["district"], state=data["state"], pincode=data["pincode"], landmark=data["landmark"], is_default=True)
                return redirect("orders:checkout_step2")
        else:
            address = Address.objects.filter(id=request.POST.get("address_id"), user=request.user).first()
            if address:
                request.session["checkout_address"] = _address_snapshot(address)
                request.session.pop("checkout_delivery_state_override", None)
                return redirect("orders:checkout_step2")
            messages.error(request, "Please select a delivery address or choose a different address.")

    return render(request, "checkout/step1.html", {
        "addresses": addresses,
        "default_address": default_address,
        "is_direct_checkout": is_direct_checkout(request),
        "indian_states": [s for s, _ in INDIAN_STATE_CHOICES],
    })


@login_required
def checkout_step2(request):
    lines = get_checkout_lines(request)
    if not lines:
        return redirect("products:list")
    unsatisfied = unsatisfied_personalization_line(request)
    if unsatisfied:
        return _redirect_to_personalize(request, unsatisfied)
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
    site_settings_obj = SiteSettings.load()
    return render(request, "checkout/step2.html", {
        "summary": summary,
        "applied_coupon": coupon,
        "is_direct_checkout": is_direct_checkout(request),
        "delivery_mode": site_settings_obj.delivery_mode,
        # The Kerala / Outside Kerala toggle only makes sense to show when
        # that's actually how delivery is being priced — for count- or
        # weight-based delivery the toggle would just be confusing/inert.
        "show_delivery_state_toggle": site_settings_obj.delivery_mode == "product_state",
    })


@login_required
@require_POST
def checkout_delivery_state(request):
    """AJAX endpoint backing the Kerala / Outside Kerala toggle on the Order
    Summary page. Stores the customer's explicit choice for the rest of
    this checkout session (takes priority over the delivery address's own
    state field — see build_summary) and returns the recalculated summary
    so the page can update the delivery charge and total in place, without
    a reload or losing scroll position."""
    from django.http import JsonResponse
    state = request.POST.get("state", "").strip().lower()
    if state not in ("kerala", "outside"):
        return JsonResponse({"error": "Invalid delivery state."}, status=400)
    request.session["checkout_delivery_state_override"] = state
    request.session.modified = True
    coupon = _get_applied_coupon(request)
    try:
        summary = build_summary(request, coupon=coupon)
    except DeliveryConfigurationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({
        "ok": True,
        "is_kerala": summary["delivery_is_kerala"],
        "subtotal": str(summary["subtotal"]),
        "discount": str(summary["discount"]),
        "delivery": str(summary["delivery"]),
        "grand_total": str(summary["grand_total"]),
    })


def _coupon_ajax_response(request, success, message, summary=None, coupon_code=""):
    """Both a JSON payload (for the no-scroll-jump AJAX flow) and a
    messages-framework fallback (for non-JS / no-JS clients) are provided."""
    from django.http import JsonResponse
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        payload = {"success": success, "message": message, "coupon_code": coupon_code}
        if summary is not None:
            payload["summary"] = {
                "subtotal": str(summary["subtotal"]),
                "discount": str(summary["discount"]),
                "delivery": str(summary["delivery"]),
                "grand_total": str(summary["grand_total"]),
            }
        return JsonResponse(payload, status=200 if success else 400)
    return None  # signal caller to fall back to messages + redirect


@login_required
@require_POST
def apply_coupon(request):
    if request.POST.get("remove"):
        request.session.pop("applied_coupon", None)
        try:
            summary = build_summary(request)
        except DeliveryConfigurationError:
            summary = None
        resp = _coupon_ajax_response(request, True, "Coupon removed.", summary)
        if resp:
            return resp
        messages.info(request, "Coupon removed.")
        return redirect("orders:checkout_step2")

    code = request.POST.get("code", "").strip()
    if not code:
        resp = _coupon_ajax_response(request, False, "Please enter a coupon code.")
        if resp:
            return resp
        messages.error(request, "Please enter a coupon code.")
        return redirect("orders:checkout_step2")

    def fail(msg):
        resp = _coupon_ajax_response(request, False, msg, coupon_code=code)
        if resp:
            return resp
        messages.error(request, msg)
        return redirect("orders:checkout_step2")

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return fail("Invalid coupon code.")

    validity_error = coupon.validity_error()
    if validity_error == "disabled":
        return fail("This coupon is currently disabled.")
    if validity_error == "not_started":
        return fail("This coupon is not active yet.")
    if validity_error == "expired":
        return fail("This coupon has expired.")

    if coupon.usage_limit and coupon.usage_count() >= coupon.usage_limit:
        return fail("This coupon has reached its usage limit.")
    if coupon.user_usage_count(request.user) >= coupon.per_user_limit:
        return fail("You have already used this coupon.")

    try:
        lines = get_checkout_lines(request)
        summary = build_summary(request)
    except DeliveryConfigurationError as exc:
        resp = _coupon_ajax_response(request, False, str(exc))
        if resp:
            return resp
        messages.error(request, str(exc))
        return redirect("orders:checkout_step1")

    if summary["subtotal"] < coupon.minimum_order:
        return fail(f"Minimum order of ₹{coupon.minimum_order} required for this coupon.")
    if not coupon.applies_to_lines(lines):
        return fail("This coupon does not apply to the items in your order.")

    request.session["applied_coupon"] = coupon.code
    summary_with_discount = build_summary(request, coupon=coupon)
    resp = _coupon_ajax_response(request, True, f"Coupon '{coupon.code}' applied.", summary_with_discount, coupon.code)
    if resp:
        return resp
    messages.success(request, f"Coupon '{coupon.code}' applied.")
    return redirect("orders:checkout_step2")


@login_required
@require_POST
def place_order(request):
    # ---- Duplicate-order prevention ----
    # A checkout_token is generated the first time the customer reaches this
    # view for the current checkout session and stored in the session. If
    # place_order is hit again for the same token (refresh, back/forward,
    # double submit, payment-page reload) we return the SAME order instead
    # of creating a second one.
    token = request.session.get("checkout_token")
    if token:
        existing = Order.objects.filter(checkout_token=token).first()
        if existing:
            from payments.models import Payment
            Payment.objects.get_or_create(order=existing)
            return redirect("payments:pay", order_number=existing.order_number)
    else:
        import uuid
        token = uuid.uuid4().hex
        request.session["checkout_token"] = token
        request.session.modified = True

    lines = get_checkout_lines(request)
    if not lines:
        messages.error(request, "Nothing to order.")
        return redirect("products:list")
    # Backend enforcement of the personalization requirement — this is the
    # real gate. Someone posting straight to this URL without ever visiting
    # the checkout pages must be blocked exactly the same way.
    unsatisfied = unsatisfied_personalization_line(request)
    if unsatisfied:
        return _redirect_to_personalize(request, unsatisfied)
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
        stock = line["variant"].stock if line.get("variant") else line["product"].stock
        if line["quantity"] > stock:
            messages.error(request, f"{line['product'].name} has insufficient stock.")
            return redirect("orders:checkout_step1")

    coupon = _get_applied_coupon(request)
    try:
        summary = build_summary(request, coupon=coupon)
    except DeliveryConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("orders:checkout_step1")

    with transaction.atomic():
        site_settings_obj = SiteSettings.load()
        delivery_mode = site_settings_obj.delivery_mode
        if delivery_mode == "count":
            rule = summary.get("delivery_rule")
            delivery_rule_label = (f"{rule.min_items}{'–' + str(rule.max_items) if rule.max_items else '+'} items") if rule else ""
            delivery_quantity = summary["total_items"]
        elif delivery_mode == "product_state":
            delivery_rule_label = "Kerala" if is_kerala_state(summary.get("delivery_state")) else "Outside Kerala"
            delivery_quantity = summary["total_items"]
        else:
            slab = summary.get("delivery_slab")
            delivery_rule_label = (f"{slab.min_weight}–{slab.max_weight if slab.max_weight else 'open'}kg") if slab else ""
            delivery_quantity = summary["total_items"]

        # Expected delivery date: each ordered product may set its own
        # "Expected Delivery Days"; when a cart mixes products, the customer
        # can only be shown one date for the whole order, so the longest
        # (most conservative) lead time wins. Products left at 0 (not set)
        # fall back to the site-wide default from Site Settings.
        default_days = site_settings_obj.default_expected_delivery_days
        max_days = max(
            (line["product"].expected_delivery_days or default_days) for line in lines
        ) if lines else default_days

        order = Order.objects.create(
            user=request.user,
            checkout_token=token,
            is_buy_now=is_direct_checkout(request),
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
            expected_delivery_date=timezone.now().date() + timezone.timedelta(days=max_days),
            delivery_method_snapshot=delivery_mode,
            delivery_quantity_snapshot=delivery_quantity,
            delivery_rule_label_snapshot=delivery_rule_label,
            delivery_state_snapshot=address_data.get("state", ""),
        )
        for line in lines:
            product = line["product"]
            variant = line.get("variant")
            qty = line["quantity"]
            # Deliberately NOT touching product/variant stock here — stock is
            # only decremented once the admin moves the order to "Processing"
            # (or a later stage), never at order placement/payment time. See
            # Order.save() + orders/services/stock.py.
            customization = None
            if line.get("customization_id"):
                customization = Customization.objects.filter(id=line["customization_id"], user=request.user).first()
            unit_price = variant.effective_price if variant else product.effective_price
            if delivery_mode == "product_state":
                line_delivery_snapshot = calculate_line_state_delivery(product, qty, address_data.get("state"))
            else:
                line_delivery_snapshot = calculate_line_delivery(product, qty)
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name_snapshot=product.name,
                price_snapshot=unit_price,
                quantity=qty,
                subtotal=line["line_total"],
                delivery_snapshot=line_delivery_snapshot,
                customization=customization,
                variant=variant,
                colour_name_snapshot=variant.colour.name if variant else "",
                colour_hex_snapshot=variant.colour.hex_code if variant else "",
                sku_snapshot=variant.sku if variant else product.sku,
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

    # The order has been placed (even though payment is still "awaiting" —
    # confirmation happens separately on the payment page). The customer no
    # longer manages these items via the cart from this point on; they're
    # tracked through this Order instead. So the cart is cleared here, right
    # when the order is placed — not held back until payment is confirmed.
    # Direct Checkout (Buy Now) never touched the cart in the first place, so
    # there's nothing to clear for that path; its own session key is cleared
    # separately once payment is confirmed (payments.views.pay_view).
    if not is_direct_checkout(request):
        from cart.cart import Cart
        Cart(request).clear()

    request.session.pop("applied_coupon", None)
    request.session.pop("checkout_address", None)
    request.session.pop("checkout_token", None)

    from payments.models import Payment
    Payment.objects.get_or_create(order=order)
    return redirect("payments:pay", order_number=order.order_number)


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.order_status == "awaiting_payment":
        # Not a real, confirmed order yet — don't show order details for it.
        return redirect("payments:pay", order_number=order.order_number)
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
    if order.order_status == "awaiting_payment":
        return redirect("payments:pay", order_number=order.order_number)
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
