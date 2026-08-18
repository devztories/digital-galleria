from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from products.models import Product
from .cart import Cart


def cart_view(request):
    cart = Cart(request)
    summary = cart.summary()
    return render(request, "cart/cart.html", {"summary": summary})


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, active=True)
    quantity = int(request.POST.get("quantity", 1))
    if quantity > product.stock:
        messages.error(request, f"Only {product.stock} in stock.")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    cart = Cart(request)
    cart.add(product, quantity)
    messages.success(request, f"{product.name} added to cart.")
    return redirect(request.META.get("HTTP_REFERER", "cart:cart"))


@require_POST
def update_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get("quantity", 1))
    if quantity > product.stock:
        messages.error(request, f"Only {product.stock} in stock.")
        quantity = product.stock
    cart = Cart(request)
    cart.set_quantity(product_id, quantity)
    return redirect("cart:cart")


@require_POST
def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
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
    quantity = int(request.POST.get("quantity", 1))
    if quantity > product.stock:
        messages.error(request, f"Only {product.stock} in stock.")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    request.session["buy_now"] = {"product_id": product.id, "quantity": quantity, "customization_id": None}
    request.session.modified = True
    return redirect("orders:checkout")
