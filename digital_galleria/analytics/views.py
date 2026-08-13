import io
import os
import zipfile
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from orders.models import Order, STATUS_CHOICES
from payments.models import PaymentProof
from products.models import Product
from categories.models import Category
from .models import Expense


def _date_ranges():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timezone.timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    year_start = today_start.replace(month=1, day=1)
    return today_start, week_start, month_start, year_start


def _sales_since(start):
    return Order.objects.filter(created_at__gte=start).exclude(status='cancelled').aggregate(
        total=Sum('grand_total'))['total'] or Decimal('0.00')


@staff_member_required
def dashboard(request):
    today_start, week_start, month_start, year_start = _date_ranges()

    sales = {
        'today': _sales_since(today_start),
        'week': _sales_since(week_start),
        'month': _sales_since(month_start),
        'year': _sales_since(year_start),
    }

    orders_qs = Order.objects.all()
    order_counts = {
        'total': orders_qs.count(),
    }
    for key, _label in STATUS_CHOICES:
        order_counts[key] = orders_qs.filter(status=key).count()

    valid_orders = orders_qs.exclude(status='cancelled')
    gross_revenue = valid_orders.aggregate(t=Sum('grand_total'))['t'] or Decimal('0.00')
    discounts = valid_orders.aggregate(t=Sum('discount_total'))['t'] or Decimal('0.00')
    delivery_revenue = valid_orders.aggregate(t=Sum('delivery_total'))['t'] or Decimal('0.00')
    net_revenue = gross_revenue

    total_expenses = Expense.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    profit_loss = net_revenue - total_expenses

    category_sales = (
        Order.objects.exclude(status='cancelled')
        .values('items__product__category__name')
        .annotate(total=Sum('items__unit_price'))
        .order_by('-total')[:6]
    )
    product_sales = (
        Order.objects.exclude(status='cancelled')
        .values('items__product_name')
        .annotate(qty=Sum('items__quantity'))
        .order_by('-qty')[:6]
    )

    recent_orders = Order.objects.all()[:8]
    pending_payments = PaymentProof.objects.filter(status='pending').select_related('order')[:8]

    return render(request, 'analytics/dashboard.html', {
        'sales': sales,
        'order_counts': order_counts,
        'gross_revenue': gross_revenue,
        'discounts': discounts,
        'delivery_revenue': delivery_revenue,
        'net_revenue': net_revenue,
        'total_expenses': total_expenses,
        'profit_loss': profit_loss,
        'category_sales': category_sales,
        'product_sales': product_sales,
        'recent_orders': recent_orders,
        'pending_payments': pending_payments,
        'status_choices': STATUS_CHOICES,
    })


@staff_member_required
def order_list(request):
    orders = Order.objects.all()
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'analytics/order_list.html', {'orders': orders, 'status_choices': STATUS_CHOICES, 'active_status': status})


@staff_member_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(STATUS_CHOICES):
                order.status = new_status
                order.save(update_fields=['status'])
                messages.success(request, 'Order status updated.')
        elif action == 'add_note':
            order.admin_note = request.POST.get('admin_note', '')
            order.save(update_fields=['admin_note'])
            messages.success(request, 'Admin note saved.')
        elif action == 'verify_payment':
            proof_id = request.POST.get('proof_id')
            proof = get_object_or_404(PaymentProof, pk=proof_id, order=order)
            proof.status = 'verified'
            proof.verified_at = timezone.now()
            proof.admin_note = request.POST.get('proof_note', '')
            proof.save()
            order.status = 'payment_verified'
            order.save(update_fields=['status'])
            messages.success(request, 'Payment verified.')
        elif action == 'reject_payment':
            proof_id = request.POST.get('proof_id')
            proof = get_object_or_404(PaymentProof, pk=proof_id, order=order)
            proof.status = 'rejected'
            proof.admin_note = request.POST.get('proof_note', '')
            proof.save()
            messages.warning(request, 'Payment rejected.')
        return redirect('analytics:order_detail', order_number=order.order_number)

    return render(request, 'analytics/order_detail.html', {
        'order': order,
        'status_choices': STATUS_CHOICES,
        'payment_proofs': order.payment_proofs.all(),
    })


@staff_member_required
def download_all_images(request, order_number):
    """Bundle every ORIGINAL customization image for this order into a ZIP,
    without re-encoding or compressing the underlying files."""
    order = get_object_or_404(Order, order_number=order_number)

    buffer = io.BytesIO()
    used_names = set()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as zf:
        for item in order.items.all():
            if not item.customization:
                continue
            for img in item.customization.images.all():
                if not img.original_file:
                    continue
                filename = img.original_filename or os.path.basename(img.original_file.name)
                base, ext = os.path.splitext(filename)
                candidate = filename
                counter = 1
                while candidate in used_names:
                    candidate = f'{base}_{counter}{ext}'
                    counter += 1
                used_names.add(candidate)
                try:
                    img.original_file.open('rb')
                    zf.writestr(candidate, img.original_file.read())
                finally:
                    img.original_file.close()

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{order.order_number}_original_images.zip"'
    return response


@staff_member_required
def download_image(request, image_id):
    from customization.models import CustomizationImage
    img = get_object_or_404(CustomizationImage, pk=image_id)
    response = FileResponse(img.original_file.open('rb'), as_attachment=True, filename=img.original_filename)
    return response


@staff_member_required
def expense_list(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount') or 0
        category = request.POST.get('category', 'other')
        date = request.POST.get('date') or timezone.now().date()
        note = request.POST.get('note', '')
        if title and amount:
            Expense.objects.create(title=title, amount=amount, category=category, date=date, note=note)
            messages.success(request, 'Expense recorded.')
            return redirect('analytics:expenses')

    expenses = Expense.objects.all()
    total = expenses.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    return render(request, 'analytics/expenses.html', {
        'expenses': expenses, 'total': total, 'categories': Expense.CATEGORY_CHOICES,
    })
