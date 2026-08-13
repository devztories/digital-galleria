from .models import Cart

def get_session_coupon(request, cart):
    from coupons.models import Coupon
    code = request.session.get('coupon_code')
    if not code:
        return None
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        request.session.pop('coupon_code', None)
        return None
    valid, _ = coupon.is_valid_now()
    if not valid:
        request.session.pop('coupon_code', None)
        return None
    return coupon

def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user, defaults={'session_key': request.session.session_key}
        )
        guest_cart = (
            Cart.objects.filter(session_key=request.session.session_key, user__isnull=True)
            .exclude(pk=cart.pk).first()
        )
        if guest_cart:
            from customization.models import Customization
            for item in guest_cart.items.select_related('customization'):
                item.cart = cart
                item.save(update_fields=['cart'])
                if item.customization_id:
                    Customization.objects.filter(
                        pk=item.customization_id, user__isnull=True
                    ).update(user=request.user)
            guest_cart.delete()
        cart.session_key = request.session.session_key
        cart.save(update_fields=['session_key'])
        return cart
    return Cart.objects.get_or_create(
        session_key=request.session.session_key, user__isnull=True
    )[0]
