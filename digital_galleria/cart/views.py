from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from coupons.models import Coupon
from products.models import Product
from .models import CartItem
from .utils import get_or_create_cart, get_session_coupon


def cart_detail(request):
    cart = get_or_create_cart(request)
    coupon = get_session_coupon(request, cart)
    discount = coupon.calculate_discount(cart.subtotal) if coupon else Decimal('0.00')
    grand_total = cart.subtotal + cart.delivery_total - discount
    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'coupon': coupon,
        'discount': discount,
        'grand_total': grand_total,
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    if not product.customizable:
        cart = get_or_create_cart(request)
        quantity = max(1, int(request.POST.get('quantity', 1) or 1))
        if product.stock < quantity:
            messages.error(request, 'Not enough stock available for this product.')
            return redirect(product.get_absolute_url())
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, customization=None,
                                                         defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            item.save(update_fields=['quantity'])
        messages.success(request, f'{product.name} added to your cart.')
        return redirect('cart:detail')
    # Customizable products must go through the customization flow
    return redirect('customization:start', product_id=product.id)


@require_POST
def update_quantity(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    quantity = max(1, quantity)
    if item.product.stock < quantity:
        messages.error(request, 'Not enough stock available.')
    else:
        item.quantity = quantity
        item.save(update_fields=['quantity'])
    return redirect('cart:detail')


@require_POST
def remove_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('cart:detail')


@require_POST
def apply_coupon(request):
    cart = get_or_create_cart(request)
    code = request.POST.get('code', '').strip().upper()
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        messages.error(request, 'Invalid coupon code.')
        return redirect('cart:detail')

    valid, reason = coupon.is_valid_now()
    if not valid:
        messages.error(request, reason)
        return redirect('cart:detail')
    if cart.subtotal < coupon.minimum_order:
        messages.error(request, f'This coupon requires a minimum order of ₹{coupon.minimum_order}.')
        return redirect('cart:detail')

    request.session['coupon_code'] = coupon.code
    messages.success(request, f'Coupon "{coupon.code}" applied!')
    next_url = request.POST.get('next', '')
    if next_url in (reverse('cart:detail'), reverse('orders:checkout')):
        return redirect(next_url)
    return redirect('cart:detail')


@require_POST
def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.info(request, 'Coupon removed.')
    return redirect('cart:detail')

