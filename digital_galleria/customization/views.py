from urllib.parse import quote
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages

from products.models import Product
from site_settings.models import SiteSettings
from .models import Customization, CustomizationImage


@staff_member_required
def download_customization_image(request, image_id):
    """
    Forces a real file download of the ORIGINAL, full-quality customization
    image — streamed straight from storage (works whether that's local disk
    in dev or Supabase Storage in production) rather than relying on the
    <a download> attribute, which browsers ignore for cross-origin CDN URLs
    without an explicit Content-Disposition header.
    """
    img = get_object_or_404(CustomizationImage, id=image_id)
    filename = img.image.name.rsplit("/", 1)[-1]
    file_obj = img.image.open("rb")
    return FileResponse(file_obj, as_attachment=True, filename=filename)


@login_required
def customize_cart_item(request, cart_key):
    """
    Item-specific customization used from the Cart / Checkout flow.
    Opens/saves a customization tied to exactly ONE cart line (product +
    colour variant) — never shared across other lines of the same product
    in a different colour, and never forces the user back to Product Detail.
    """
    from cart.cart import Cart
    cart = Cart(request)
    line = cart.get_line(cart_key)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not line:
        if is_ajax:
            return JsonResponse({"error": "Cart item not found."}, status=404)
        messages.error(request, "Cart item not found.")
        return redirect("cart:cart")

    product = line["product"]
    if not product.customizable:
        if is_ajax:
            return JsonResponse({"error": "This product is not customizable."}, status=400)
        messages.error(request, "This product is not customizable.")
        return redirect("cart:cart")

    settings_obj = SiteSettings.load()
    max_images = (
        product.max_customization_images
        if product.max_customization_images > 0
        else settings_obj.customization_max_images
    )

    existing = None
    if line.get("customization_id"):
        existing = Customization.objects.filter(
            id=line["customization_id"], user=request.user, product=product
        ).prefetch_related("images").first()

    if request.method == "POST":
        details = request.POST.get("details", "").strip()
        uploads = request.FILES.getlist("reference_images")
        allowed = {
            x.strip().lower().lstrip(".")
            for x in (settings_obj.customization_allowed_formats or "jpg,jpeg,png,webp").split(",")
            if x.strip()
        }
        max_size = settings_obj.customization_max_image_size_mb * 1024 * 1024
        via_whatsapp = request.POST.get("via_whatsapp") == "on"

        # Personalization is satisfied by EITHER an uploaded image OR the
        # WhatsApp checkbox — never both required. This also has to account
        # for images/whatsapp already saved on an existing customization for
        # this cart line (e.g. re-opening the drawer to edit details only).
        already_satisfied = bool(existing) and (existing.images.exists() or existing.via_whatsapp)

        error = None
        if uploads and len(uploads) > max_images:
            error = f"You can upload up to {max_images} images."
        elif any(getattr(f, "size", 0) > max_size for f in uploads):
            error = f"Each image must be at most {settings_obj.customization_max_image_size_mb} MB."
        elif any((".") not in f.name or f.name.rsplit(".", 1)[-1].lower() not in allowed for f in uploads):
            error = "One or more image formats are not allowed."
        elif not uploads and not via_whatsapp and not already_satisfied:
            error = "Please upload an image or enable WhatsApp checkout to continue."

        if error:
            if is_ajax:
                return JsonResponse({"error": error}, status=400)
            messages.error(request, error)
            return redirect("cart:cart")

        if existing:
            # "Edit Customization" — original files are preserved (this endpoint
            # only appends; images are never destructively replaced unless the
            # customer explicitly deletes one).
            custom = existing
            custom.details = details
            if via_whatsapp and not custom.via_whatsapp:
                custom.via_whatsapp = True
                custom.save(update_fields=["details", "via_whatsapp"])
            else:
                custom.save(update_fields=["details"])
            start_order = custom.images.count()
        else:
            custom = Customization.objects.create(user=request.user, product=product, details=details, via_whatsapp=via_whatsapp)
            start_order = 0

        for idx, upload in enumerate(uploads):
            # Original file is stored as-is — full resolution, original
            # extension, no server-side re-compression.
            CustomizationImage.objects.create(customization=custom, image=upload, display_order=start_order + idx)

        cart.set_customization(cart_key, custom.id)

        # ---- WhatsApp customization (mirrors the main Product Detail
        # customize page — available from the cart drawer too, per spec). ----
        if request.POST.get("action") == "whatsapp" and settings_obj.whatsapp_customization_enabled:
            message = (settings_obj.whatsapp_default_message or "Hello Digital Galleria, I am sending customization images here.").strip()
            if settings_obj.whatsapp_include_product_name:
                message += f"\n\nProduct: {product.name}"
            if line.get("variant"):
                message += f"\nColour: {line['variant'].colour.name}"
            if settings_obj.whatsapp_include_order_number:
                message += f"\nCustomization: #{custom.id}"
            if settings_obj.whatsapp_include_customer_name:
                message += f"\nCustomer: {request.user.name}"
            message += f"\nQuantity: {line['quantity']}"
            message += "\nCustomization: Via WhatsApp"
            if details:
                message += f"\nDescription: {details}"
            custom.whatsapp_message = message
            custom.save(update_fields=["whatsapp_message"])

            whatsapp_url = ""
            if settings_obj.whatsapp_chat_url:
                separator = "&" if "?" in settings_obj.whatsapp_chat_url else "?"
                whatsapp_url = f"{settings_obj.whatsapp_chat_url}{separator}text={quote(message)}"
            elif settings_obj.whatsapp_number:
                wa_number = "".join(ch for ch in settings_obj.whatsapp_number if ch.isdigit() or ch == "+")
                whatsapp_url = f"https://wa.me/{wa_number.lstrip('+')}?text={quote(message)}"

            if whatsapp_url:
                if is_ajax:
                    return JsonResponse({"ok": True, "whatsapp_url": whatsapp_url, "customization_id": custom.id})
                return redirect(whatsapp_url)
            error = "WhatsApp customization is enabled, but the administrator has not configured a WhatsApp chat link."
            if is_ajax:
                return JsonResponse({"error": error}, status=400)
            messages.error(request, error)
            return redirect("cart:cart")

        if is_ajax:
            return JsonResponse({
                "ok": True,
                "customization_id": custom.id,
                "image_count": custom.images.count(),
                "details": custom.details,
                "images": [img.image.url for img in custom.images.all()],
            })
        messages.success(request, "Customization saved.")
        return redirect("cart:cart")

    # GET: render the drawer/modal fragment for AJAX injection into the Cart page.
    return render(request, "customization/_cart_drawer.html", {
        "product": product,
        "variant": line.get("variant"),
        "cart_key": cart_key,
        "existing": existing,
        "max_images": max_images,
        "site_settings": settings_obj,
    })


@login_required
def remove_customization_image(request, image_id):
    """Deletes a single reference image from an in-progress cart-item customization."""
    img = get_object_or_404(CustomizationImage, id=image_id, customization__user=request.user)
    img.image.delete(save=False)
    img.delete()
    return JsonResponse({"ok": True})


@login_required
def customize_product(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True, customizable=True)
    settings_obj = SiteSettings.load()
    if not settings_obj.customization_enabled:
        messages.info(request, "Customization is currently unavailable.")
        return redirect("products:detail", slug=product.slug)

    # Colour carried in from Product Detail's "Buy Now" link (?variant_id=) or
    # from the form re-post — kept alive through the whole customize → buy flow.
    variant = None
    variant_id = request.POST.get("variant_id") or request.GET.get("variant_id")
    if variant_id:
        from products.models import ProductVariant
        variant = ProductVariant.objects.filter(id=variant_id, product=product, active=True).select_related("colour").first()

    whatsapp_url = ""
    auto_open_whatsapp = False

    # A product can override the site-wide image limit; 0 means
    # "use the site default" (admin-configurable per product).
    max_images = (
        product.max_customization_images
        if product.max_customization_images > 0
        else settings_obj.customization_max_images
    )

    # Prefills the quantity field when arriving from an existing cart line
    # (Cart → Buy Now on a customizable product) so it matches what was in
    # the cart instead of silently resetting to 1.
    stock_for_prefill = variant.stock if variant else product.stock
    try:
        initial_quantity = max(1, min(int(request.GET.get("quantity", 1)), stock_for_prefill or 1))
    except (TypeError, ValueError):
        initial_quantity = 1

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
        stock = variant.stock if variant else product.stock

        if len(uploads) > max_images:
            messages.error(request, f"You can upload up to {max_images} images.")
        elif any(getattr(f, "size", 0) > max_size for f in uploads):
            messages.error(request, f"Each image must be at most {settings_obj.customization_max_image_size_mb} MB.")
        elif any(
            ("." not in f.name) or (f.name.rsplit(".", 1)[-1].lower() not in allowed)
            for f in uploads
        ):
            messages.error(request, "One or more image formats are not allowed.")
        elif not uploads and not via_whatsapp:
            # Backend enforcement of "image OR WhatsApp" — mirrors the
            # frontend check so this can't be skipped by disabling JS,
            # editing the form, or posting directly to this URL.
            messages.error(request, "Please upload an image or enable WhatsApp checkout to continue.")
        else:
            try:
                quantity = max(1, min(int(request.POST.get("quantity", 1) or 1), stock))
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
                if variant:
                    message += f"\nColour: {variant.colour.name}"
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
                # Buy Now → Customize → Checkout: this is that final hand-off —
                # the colour variant (if any) rides along in the same buy_now session.
                request.session["buy_now"] = {
                    "product_id": product.id,
                    "variant_id": variant.id if variant else None,
                    "quantity": quantity,
                    "customization_id": custom.id,
                }
                request.session.modified = True
                return redirect("orders:checkout")

            if action == "cart":
                from cart.cart import Cart
                cart = Cart(request)
                cart.add(product, quantity, customization_id=custom.id, variant_id=variant.id if variant else None)
                messages.success(request, "Customized product added to cart.")
                return redirect("cart:cart")

    return render(
        request,
        "customization/index.html",
        {
            "product": product,
            "variant": variant,
            "site_settings": settings_obj,
            "max_images": max_images,
            "initial_quantity": initial_quantity,
            "whatsapp_url": whatsapp_url,
            "auto_open_whatsapp": auto_open_whatsapp,
        },
    )
