from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from cart.utils import get_or_create_cart, get_session_coupon
from payments.models import PaymentProof
from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required(login_url='accounts:login')
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:detail')

    coupon = get_session_coupon(request, cart)
    discount = coupon.calculate_discount(cart.subtotal) if coupon else Decimal('0.00')
    grand_total = cart.subtotal + cart.delivery_total - discount

    initial = {}
    if request.user.is_authenticated:
        initial = {'full_name': request.user.display_name, 'email': request.user.email, 'phone': request.user.phone}

    if request.method == 'POST':
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            # Re-validate stock server-side before committing the order
            for item in cart.items_qs:
                if item.quantity > item.product.stock:
                    messages.error(request, f'{item.product.name} no longer has enough stock.')
                    return redirect('cart:detail')

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                district=form.cleaned_data['district'],
                state=form.cleaned_data['state'],
                pincode=form.cleaned_data['pincode'],
                delivery_notes=form.cleaned_data.get('delivery_notes', ''),
                gender_snapshot=getattr(request.user, 'gender', '') if request.user.is_authenticated else '',
                subtotal=cart.subtotal,
                delivery_total=cart.delivery_total,
                discount_total=discount,
                grand_total=grand_total,
                coupon_code=coupon.code if coupon else '',
                status='pending_payment',
            )

            for item in cart.items_qs:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    customization=item.customization,
                    product_name=item.product.name,
                    unit_price=item.product.price,
                    delivery_charge=item.product.delivery_charge,
                    quantity=item.quantity,
                    recipient_name=item.customization.recipient_name if item.customization else '',
                    custom_message=item.customization.custom_message if item.customization else '',
                    via_whatsapp=item.customization.via_whatsapp if item.customization else False,
                )
                # Decrement stock server-side
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save(update_fields=['stock'])

            if coupon:
                coupon.times_used += 1
                coupon.save(update_fields=['times_used'])
                request.session.pop('coupon_code', None)

            cart.items.all().delete()

            return redirect('orders:payment', order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {
        'form': form, 'cart': cart, 'coupon': coupon, 'discount': discount, 'grand_total': grand_total,
    })


@login_required(login_url='accounts:login')
def payment_page(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == 'POST':
        screenshot = request.FILES.get('screenshot')
        if not screenshot:
            messages.error(request, 'Please upload your payment screenshot.')
        else:
            PaymentProof.objects.create(order=order, screenshot=screenshot)
            order.status = 'payment_submitted'
            order.save(update_fields=['status'])
            messages.success(request, 'Payment proof submitted. We will verify it shortly.')
            return redirect('orders:track', order_number=order.order_number)
    return render(request, 'orders/payment.html', {'order': order})


@login_required(login_url='accounts:login')
def track_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    success_key = f'order_success_seen_{order.order_number}'
    show_success = order.status == 'payment_submitted' and not request.session.get(success_key)
    if show_success:
        request.session[success_key] = True
    return render(request, 'orders/track.html', {'order': order, 'show_success': show_success})
