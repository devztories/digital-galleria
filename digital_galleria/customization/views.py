from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages

from products.models import Product
from site_settings.models import SiteSettings
from .models import Customization, CustomizationImage


@login_required
def customize_product(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True, customizable=True)
    settings_obj = SiteSettings.load()
    if not settings_obj.customization_enabled:
        messages.info(request, "Customization is currently unavailable.")
        return redirect("products:detail", slug=product.slug)

    whatsapp_url = ""
    auto_open_whatsapp = False

    # A product can override the site-wide image limit; 0 means
    # "use the site default" (admin-configurable per product).
    max_images = (
        product.max_customization_images
        if product.max_customization_images > 0
        else settings_obj.customization_max_images
    )

    if request.method == "POST":
        details = request.POST.get("details", "").strip()
        via_whatsapp = request.POST.get("via_whatsapp") == "on"
        uploads = request.FILES.getlist("reference_images")
        allowed = {
            x.strip().lower().lstrip(".")
            for x in (settings_obj.customization_allowed_formats or "jpg,jpeg,png,webp").split(",")
            if x.strip()
        }
        max_size = settings_obj.customization_max_image_size_mb * 1024 * 1024

        if len(uploads) > max_images:
            messages.error(request, f"You can upload up to {max_images} images.")
        elif any(getattr(f, "size", 0) > max_size for f in uploads):
            messages.error(request, f"Each image must be at most {settings_obj.customization_max_image_size_mb} MB.")
        elif any(
            ("." not in f.name) or (f.name.rsplit(".", 1)[-1].lower() not in allowed)
            for f in uploads
        ):
            messages.error(request, "One or more image formats are not allowed.")
        else:
            try:
                quantity = max(1, min(int(request.POST.get("quantity", 1) or 1), product.stock))
            except (TypeError, ValueError):
                quantity = 1

            custom = Customization.objects.create(
                user=request.user,
                product=product,
                details=details,
                via_whatsapp=via_whatsapp,
            )
            for idx, upload in enumerate(uploads):
                CustomizationImage.objects.create(
                    customization=custom, image=upload, display_order=idx
                )

            action = request.POST.get("action")

            if action == "whatsapp" and via_whatsapp:
                message = (
                    settings_obj.whatsapp_default_message
                    or "Hello Digital Galleria, I am sending customization images here."
                ).strip()
                if settings_obj.whatsapp_include_product_name:
                    message += f"\n\nProduct: {product.name}"
                if settings_obj.whatsapp_include_order_number:
                    message += f"\nCustomization: #{custom.id}"
                if settings_obj.whatsapp_include_customer_name:
                    message += f"\nCustomer: {request.user.name}"
                message += f"\nQuantity: {quantity}"
                message += "\nCustomization: Via WhatsApp"
                if details:
                    message += f"\nDescription: {details}"

                custom.whatsapp_message = message
                custom.save(update_fields=["whatsapp_message"])

                if settings_obj.whatsapp_chat_url:
                    separator = "&" if "?" in settings_obj.whatsapp_chat_url else "?"
                    whatsapp_url = f"{settings_obj.whatsapp_chat_url}{separator}text={quote(message)}"
                    auto_open_whatsapp = True
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"ok": True, "whatsapp_url": whatsapp_url})
                elif settings_obj.whatsapp_number:
                    wa_number = "".join(ch for ch in settings_obj.whatsapp_number if ch.isdigit() or ch == "+")
                    whatsapp_url = f"https://wa.me/{wa_number.lstrip('+')}?text={quote(message)}"
                    auto_open_whatsapp = True
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"ok": True, "whatsapp_url": whatsapp_url})
                else:
                    messages.error(request, "WhatsApp customization is enabled, but the administrator has not configured a WhatsApp chat link.")

            if action == "direct_checkout":
                request.session["buy_now"] = {
                    "product_id": product.id,
                    "quantity": quantity,
                    "customization_id": custom.id,
                }
                request.session.modified = True
                return redirect("orders:checkout")

            if action == "cart":
                from cart.cart import Cart
                cart = Cart(request)
                cart.add(product, quantity, customization_id=custom.id)
                messages.success(request, "Customized product added to cart.")
                return redirect("cart:cart")

    return render(
        request,
        "customization/index.html",
        {
            "product": product,
            "site_settings": settings_obj,
            "max_images": max_images,
            "whatsapp_url": whatsapp_url,
            "auto_open_whatsapp": auto_open_whatsapp,
        },
    )
