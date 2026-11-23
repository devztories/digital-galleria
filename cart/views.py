from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST

from products.models import Product, ProductVariant
from .cart import Cart


def _get_variant(product, request):
    """Resolve the variant referenced by a form's hidden 'variant_id' field, if any."""
    variant_id = request.POST.get("variant_id")
    if not variant_id:
        return None
    return ProductVariant.objects.filter(id=variant_id, product=product, active=True).select_related("colour").first()


def cart_view(request):
    cart = Cart(request)
    summary = cart.summary()
    return render(request, "cart/cart.html", {"summary": summary})


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, active=True)
    variant = _get_variant(product, request)
    quantity = int(request.POST.get("quantity", 1))
    stock = variant.stock if variant else product.stock
    if variant is None and product.has_colour_variants:
        messages.error(request, "Please select a colour before adding to cart.")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    if quantity > stock:
        messages.error(request, f"Only {stock} in stock.")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    cart = Cart(request)
    cart.add(product, quantity, variant_id=variant.id if variant else None)
    label = f"{product.name} ({variant.colour.name})" if variant else product.name
    messages.success(request, f"{label} added to cart.")
    return redirect(request.META.get("HTTP_REFERER", "cart:cart"))


@require_POST
def update_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant = _get_variant(product, request)
    quantity = int(request.POST.get("quantity", 1))
    stock = variant.stock if variant else product.stock
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if quantity > stock:
        if is_ajax:
            return JsonResponse({"error": f"Only {stock} in stock."}, status=400)
        messages.error(request, f"Only {stock} in stock.")
        quantity = stock
    cart = Cart(request)
    cart.set_quantity(product_id, quantity, variant_id=variant.id if variant else None)
    if is_ajax:
        summary = cart.summary()
        line = next((l for l in summary["lines"] if l["product"].id == product.id and (l["variant"].id if l["variant"] else None) == (variant.id if variant else None)), None)
        return JsonResponse({
            "removed": line is None,
            "quantity": line["quantity"] if line else 0,
            "line_total": str(line["line_total"]) if line else "0.00",
            "summary": {
                "subtotal": str(summary["subtotal"]),
                "discount": str(summary["discount"]),
                "delivery": str(summary["delivery"]),
                "grand_total": str(summary["grand_total"]),
                "total_weight": str(summary["total_weight"]),
            },
        })
    return redirect("cart:cart")


@require_POST
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant = _get_variant(product, request)
    cart = Cart(request)
    cart.remove(product_id, variant_id=variant.id if variant else None)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        summary = cart.summary()
        return JsonResponse({
            "ok": True,
            "summary": {
                "subtotal": str(summary["subtotal"]),
                "discount": str(summary["discount"]),
                "delivery": str(summary["delivery"]),
                "grand_total": str(summary["grand_total"]),
                "total_weight": str(summary["total_weight"]),
            },
        })
    messages.info(request, "Item removed from cart.")
    return redirect("cart:cart")


@require_POST
def clear_cart(request):
    Cart(request).clear()
    return redirect("cart:cart")


@require_POST
def buy_now(request, product_id):
    """Direct Checkout: sets a standalone buy-now session, does NOT touch cart."""
    product = get_object_or_404(Product, id=product_id, active=True)
    variant = _get_variant(product, request)
    quantity = int(request.POST.get("quantity", 1))
    stock = variant.stock if variant else product.stock
    if variant is None and product.has_colour_variants:
        messages.error(request, "Please select a colour before continuing.")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    if quantity > stock:
        messages.error(request, f"Only {stock} in stock.")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    request.session["buy_now"] = {
        "product_id": product.id,
        "variant_id": variant.id if variant else None,
        "quantity": quantity,
        "customization_id": None,
    }
    request.session.modified = True
    if product.customizable:
        # Buy Now on a customizable product must always go back through
        # Personalization first — even if this exact product was already
        # customized earlier (e.g. in the cart). customization_id above is
        # deliberately left None so a fresh personalization is required.
        from django.urls import reverse
        url = reverse("customization:customize", args=[product.slug])
        params = []
        if variant:
            params.append(f"variant_id={variant.id}")
        params.append(f"quantity={quantity}")
        url += "?" + "&".join(params)
        return redirect(url)
    return redirect("orders:checkout")
