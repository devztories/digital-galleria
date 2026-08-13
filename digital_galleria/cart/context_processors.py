def cart_summary(request):
    """
    Lightweight cart badge info for the header. Avoids creating a cart row
    on every request; only reads an existing one if present.
    """
    from .models import Cart
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first() if session_key else None
    if cart:
        count = cart.total_quantity
    return {'cart_item_count': count}
