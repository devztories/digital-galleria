from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

from orders.models import Order
from .models import Payment
from site_settings.models import SiteSettings


@login_required
def pay_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    payment, _ = Payment.objects.get_or_create(order=order)
    settings_obj = SiteSettings.load()
    if not settings_obj.payment_available:
        return render(request, "payments/payment.html", {"order": order, "payment": payment, "site_settings": settings_obj, "payment_disabled": True})

    payment_error = ""
    if request.method == "POST":
        transaction_reference = request.POST.get("transaction_reference", "").strip()
        proof = request.FILES.get("proof_image")
        # A payment confirmation is valid only when at least one verifiable
        # artifact is supplied: transaction/reference ID OR payment proof.
        if not transaction_reference and not proof and not payment.proof_image:
            payment_error = "Enter a transaction/reference ID or upload a payment screenshot before submitting."
        else:
            if transaction_reference:
                payment.transaction_reference = transaction_reference
            if proof:
                payment.proof_image = proof
            payment.rejection_note = ""
            payment.save()
            if order.payment_status == "rejected":
                order.payment_status = "pending"
                order.save(update_fields=["payment_status"])
            return redirect("payments:success", order_number=order.order_number)

    return render(request, "payments/payment.html", {
        "order": order, "payment": payment, "site_settings": settings_obj, "payment_error": payment_error
    })


@login_required
def qr_download(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    site = SiteSettings.load()
    if not site.qr_code:
        raise Http404("QR code is not configured")
    try:
        return FileResponse(site.qr_code.open("rb"), as_attachment=True, filename="digital-galleria-upi-qr.png")
    except (FileNotFoundError, OSError):
        raise Http404("QR code is unavailable")


@login_required
def success_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.payment_status == "rejected":
        return render(request, "payments/rejected.html", {"order": order})
    return render(request, "payments/success.html", {"order": order, "site_settings": SiteSettings.load()})
