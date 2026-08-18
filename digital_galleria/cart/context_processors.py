from .cart import Cart


def cart_context(request):
    try:
        cart = Cart(request)
        return {"cart_count": len(cart)}
    except Exception:
        return {"cart_count": 0}
