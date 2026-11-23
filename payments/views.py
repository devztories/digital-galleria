import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

from orders.models import Order
from .models import Payment
from site_settings.models import SiteSettings


@login_required
@never_cache
def pay_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    payment, _ = Payment.objects.get_or_create(order=order)
    settings_obj = SiteSettings.load()

    # The order is only ever "confirmed" the moment payment proof passes
    # validation below (see the POST branch). Reaching this page, opening
    # it, refreshing it, or pressing Back must never confirm an order by
    # itself. If this order has already been confirmed once (order_status
    # moved past "awaiting_payment") there's nothing left to submit here —
    # send the customer straight to their order status, EXCEPT when the
    # admin rejected the payment and the customer needs to resubmit proof.
    if order.order_status != "awaiting_payment" and order.payment_status != "rejected":
        return redirect("payments:success", order_number=order.order_number)

    if not settings_obj.payment_available:
        return render(request, "payments/payment.html", {"order": order, "payment": payment, "site_settings": settings_obj, "payment_disabled": True})

    payment_error = ""
    if request.method == "POST":
        transaction_reference = request.POST.get("transaction_reference", "").strip()
        proof = request.FILES.get("proof_image")
        # A payment confirmation is valid only when at least one verifiable
        # artifact is supplied: transaction/reference ID OR UTR/transaction
        # reference number. Both optional individually, at least one required.
        # This is enforced here regardless of what the browser already sent
        # (JS validation, disabled JS, direct POSTs, dev tools, etc. all land
        # here) — this check is the real gate.
        if not transaction_reference and not proof and not payment.proof_image:
            payment_error = "Please upload the payment screenshot or enter the UTR number to continue."
        else:
            if transaction_reference:
                payment.transaction_reference = transaction_reference
            if proof:
                payment.proof_image = proof
            payment.rejection_note = ""
            payment.save()

            was_unconfirmed = order.order_status == "awaiting_payment"
            update_fields = []
            if was_unconfirmed:
                order.order_status = "verified"
                update_fields.append("order_status")
            if order.payment_status == "rejected":
                order.payment_status = "pending"
                update_fields.append("payment_status")
            if update_fields:
                order.save(update_fields=update_fields)

            # The cart itself was already cleared back when this order was
            # placed (orders.views.place_order) — not held back until now.
            # This is just a safety-net no-op for that normal case; it only
            # does real work for the (buy-now) direct-checkout session, which
            # never touches the cart and is cleared here for the first time.
            if was_unconfirmed:
                if order.is_buy_now:
                    request.session.pop("buy_now", None)
                    request.session.modified = True
                else:
                    from cart.cart import Cart
                    Cart(request).clear()

            return redirect("payments:success", order_number=order.order_number)

    return render(request, "payments/payment.html", {
        "order": order, "payment": payment, "site_settings": settings_obj, "payment_error": payment_error
    })


def _find_qr_path():
    """The UPI QR picture. Looked up straight from the project's static/ folder
    (no collectstatic / manifest needed), so it can never 'fail to load' because
    of static-file hashing. Just keep one of these files committed:
        static/img/payment-qr.png   (any of .png .jpg .jpeg .webp)
        static/image_library/payment-qr.*   (also accepted)
    """
    base = Path(settings.BASE_DIR) / "static"
    for folder in ("img", "image_library", "images"):
        for stem in ("payment-qr", "payment_qr", "qr"):
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                path = base / folder / f"{stem}{ext}"
                if path.is_file():
                    return path
    found = finders.find("img/payment-qr.png")
    return Path(found) if found else None


@never_cache
def qr_image(request):
    """Inline QR image used by the payment page (<img src=...>)."""
    qr_path = _find_qr_path()
    if not qr_path:
        raise Http404("QR code is unavailable")
    ctype = mimetypes.guess_type(qr_path.name)[0] or "image/png"
    return FileResponse(open(qr_path, "rb"), content_type=ctype)


@login_required
def qr_download(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    qr_path = _find_qr_path()
    if not qr_path:
        raise Http404("QR code is unavailable")
    return FileResponse(open(qr_path, "rb"), as_attachment=True,
                        filename=f"digital-galleria-upi-qr{qr_path.suffix}")


@login_required
@never_cache
def success_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.order_status == "awaiting_payment":
        # Nothing has been confirmed yet — send them back to submit proof
        # instead of showing anything that looks like a success page.
        return redirect("payments:pay", order_number=order.order_number)
    if order.payment_status == "rejected":
        return render(request, "payments/rejected.html", {"order": order})
    return render(request, "payments/success.html", {"order": order, "site_settings": SiteSettings.load()})
