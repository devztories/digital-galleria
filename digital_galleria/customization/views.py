import os
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from products.models import Product
from cart.models import CartItem
from cart.utils import get_or_create_cart
from .forms import CustomizationForm
from .models import Customization, CustomizationImage

try:
    from PIL import Image
except ImportError:
    Image = None


def start_customization(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True, customizable=True)
    if request.method == 'POST':
        form = CustomizationForm(request.POST)
        via_whatsapp = request.POST.get('via_whatsapp') == 'on'
        uploaded_files = request.FILES.getlist('images')

        if not via_whatsapp:
            valid, error = _validate_images(uploaded_files, product.max_custom_images)
            if not valid:
                messages.error(request, error)
                return render(request, 'customization/customize.html', {
                    'product': product, 'form': form,
                })

        if form.is_valid():
            customization = form.save(commit=False)
            customization.product = product
            customization.user = request.user if request.user.is_authenticated else None
            customization.via_whatsapp = via_whatsapp
            customization.save()

            if not via_whatsapp:
                for f in uploaded_files:
                    _save_original_image(customization, f)

            cart = get_or_create_cart(request)
            quantity = max(1, int(request.POST.get('quantity', 1) or 1))
            CartItem.objects.create(cart=cart, product=product, customization=customization, quantity=quantity)

            next_action = request.POST.get('next_action', 'cart')
            if next_action == 'checkout':
                return redirect('orders:checkout')
            messages.success(request, 'Your personalized item was added to the cart.')
            return redirect('cart:detail')
    else:
        form = CustomizationForm()

    return render(request, 'customization/customize.html', {'product': product, 'form': form})


def _validate_images(files, max_images):
    if not files:
        return False, 'Please upload at least one image, or choose WhatsApp instead.'
    if len(files) > max_images:
        return False, f'You can upload a maximum of {max_images} images for this product.'
    max_bytes = settings.MAX_CUSTOM_IMAGE_SIZE_MB * 1024 * 1024
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return False, f'"{f.name}" is not a supported image type.'
        if getattr(f, 'content_type', None) and f.content_type not in settings.ALLOWED_IMAGE_MIME_TYPES:
            return False, f'"{f.name}" failed file-type validation.'
        if f.size > max_bytes:
            return False, f'"{f.name}" is larger than {settings.MAX_CUSTOM_IMAGE_SIZE_MB}MB.'
    return True, ''


def _save_original_image(customization, uploaded_file):
    """Persist the ORIGINAL uploaded file untouched. No re-encoding/resizing here."""
    width = height = None
    if Image is not None:
        try:
            uploaded_file.seek(0)
            img = Image.open(uploaded_file)
            width, height = img.size
            uploaded_file.seek(0)
        except Exception:
            pass

    CustomizationImage.objects.create(
        customization=customization,
        original_file=uploaded_file,
        original_filename=uploaded_file.name,
        file_size=uploaded_file.size,
        content_type=getattr(uploaded_file, 'content_type', ''),
        width=width,
        height=height,
    )
