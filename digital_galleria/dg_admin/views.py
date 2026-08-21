from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings

from .decorators import dg_admin_required, dg_superuser_required
from .models import AuditLog, log_action
from .forms import (
    ProductForm, ProductVariantForm, ColourForm, CategoryForm, CouponForm, SiteSettingsForm, ThemeSettingsForm, PageThemeForm, AssetSettingForm, AnimationSettingsForm, DeliveryCountRuleForm,
    HeroSlideForm, StoryForm, AdvertisementForm, FAQForm, OfferForm, DeliveryWeightSlabForm,
)

from products.models import Product, ProductVariant, Colour, VariantImage
from categories.models import Category
from orders.models import Order, OrderItem, DeliveryWeightSlab, DeliveryCountRule
from payments.models import Payment
from accounts.models import User
from coupons.models import Coupon
from site_settings.models import SiteSettings, HeroSlide, Story, Advertisement, FAQ, Offer, ThemeSettings, PageTheme, AssetSetting, AnimationSettings, PAGE_KEYS
from customization.models import Customization
from chatbot.models import ChatConversation, ChatMessage
from orders.services.delivery import calculate_total_delivery


# ---------- Dashboard ----------

@dg_admin_required
def dashboard(request):
    today = timezone.now().date()
    # Orders still "awaiting_payment" have no proof submitted yet and aren't
    # real placed orders — exclude them from every admin figure below so
    # abandoned/incomplete checkouts never inflate revenue or order counts.
    orders = Order.objects.exclude(order_status__in=["cancelled", "awaiting_payment"])

    total_revenue = orders.aggregate(s=Sum("grand_total"))["s"] or Decimal("0.00")
    today_orders_qs = Order.objects.exclude(order_status="awaiting_payment").filter(created_date__date=today)
    today_revenue = today_orders_qs.exclude(order_status="cancelled").aggregate(s=Sum("grand_total"))["s"] or Decimal("0.00")

    stats = {
        "total_revenue": total_revenue,
        "total_orders": Order.objects.exclude(order_status="awaiting_payment").count(),
        "today_orders": today_orders_qs.count(),
        "today_revenue": today_revenue,
        "pending_orders": Order.objects.filter(order_status="verified").count(),
        "processing_orders": Order.objects.filter(order_status="processing").count(),
        "shipped_orders": Order.objects.filter(order_status="shipped").count(),
        "delivered_orders": Order.objects.filter(order_status="delivered").count(),
        "cancelled_orders": Order.objects.filter(order_status="cancelled").count(),
        "total_customers": User.objects.filter(is_staff=False).count(),
        "active_products": Product.objects.filter(active=True).count(),
        "low_stock_products": Product.objects.filter(stock__lte=SiteSettings.load().low_stock_threshold, stock__gt=0).count(),
        "pending_payments": Order.objects.filter(payment_status="pending").exclude(order_status="awaiting_payment").count(),
    }

    recent_orders = Order.objects.exclude(order_status="awaiting_payment")[:10]
    low_stock = Product.objects.filter(stock__lte=SiteSettings.load().low_stock_threshold).order_by("stock")[:10]
    pending_payments = Order.objects.filter(payment_status="pending").exclude(order_status="awaiting_payment").select_related("payment")[:10]
    upcoming_deliveries = Order.objects.filter(
        expected_delivery_date__isnull=False, order_status__in=["verified", "processing", "shipped"]
    ).order_by("expected_delivery_date")[:10]

    top_products = (
        OrderItem.objects.values("product__name", "product_id")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("subtotal"))
        .order_by("-units_sold")[:5]
    )
    top_categories = (
        OrderItem.objects.filter(product__category__isnull=False)
        .values("product__category__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("subtotal"))
        .order_by("-units_sold")[:5]
    )

    return render(request, "dg_admin/dashboard.html", {
        "stats": stats, "recent_orders": recent_orders, "low_stock": low_stock,
        "pending_payments": pending_payments, "upcoming_deliveries": upcoming_deliveries,
        "top_products": top_products, "top_categories": top_categories,
    })


# ---------- Products ----------

@dg_admin_required
def product_list(request):
    products = Product.objects.all().prefetch_related("variants__colour")
    q = request.GET.get("q")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    paginator = Paginator(products, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dg_admin/product_list.html", {"page_obj": page_obj, "q": q or ""})


@dg_admin_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            is_new = product is None
            obj = form.save()
            gallery_files = request.FILES.getlist("gallery_images")
            if gallery_files:
                existing_max = obj.images.order_by("-display_order").values_list("display_order", flat=True).first()
                next_order = (existing_max + 1) if existing_max is not None else 0
                from products.models import ProductImage
                for upload in gallery_files:
                    ProductImage.objects.create(product=obj, image=upload, display_order=next_order)
                    next_order += 1
            log_action(request, "Admin updated product" if pk else "Admin created product", obj.name)
            if is_new:
                # Land back on the edit page (not the list) so colour
                # variants + their images can be added right away.
                messages.success(request, "Product created. Now add colour variants below, if this product comes in multiple colours.")
                return redirect("dg_admin:product_edit", pk=obj.pk)
            messages.success(request, "Product saved.")
            return redirect("dg_admin:product_list")
    else:
        form = ProductForm(instance=product)
    variants = product.variants.select_related("colour").prefetch_related("images") if product else []
    return render(request, "dg_admin/product_form.html", {
        "form": form,
        "title": "Product",
        "product": product,
        "product_gallery": product.images.all() if product else [],
        "allow_gallery_upload": True,
        "variants": variants,
        "colours": Colour.objects.filter(active=True),
        "variant_form": ProductVariantForm(),
    })


@dg_admin_required
def product_variant_add(request, product_id):
    """Add a colour variant to a product AND upload its images in one submit —
    the admin never has to save the variant first before adding images."""
    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            images = request.FILES.getlist("images")
            for idx, upload in enumerate(images):
                VariantImage.objects.create(variant=variant, image=upload, display_order=idx, is_primary=(idx == 0))
            log_action(request, "Admin added colour variant", f"{product.name} — {variant.colour.name}")
            messages.success(request, f"Added {variant.colour.name} with {len(images)} image(s).")
        else:
            messages.error(request, "Could not add colour variant: " + "; ".join(f"{k}: {v[0]}" for k, v in form.errors.items()))
    return redirect("dg_admin:product_edit", pk=product_id)


@dg_admin_required
def product_variant_edit(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    if request.method == "POST":
        form = ProductVariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist("images")
            start_order = variant.images.count()
            for idx, upload in enumerate(images):
                VariantImage.objects.create(variant=variant, image=upload, display_order=start_order + idx)
            log_action(request, "Admin updated colour variant", f"{variant.product.name} — {variant.colour.name}")
            messages.success(request, f"{variant.colour.name} updated.")
        else:
            messages.error(request, "Could not update colour variant: " + "; ".join(f"{k}: {v[0]}" for k, v in form.errors.items()))
    return redirect("dg_admin:product_edit", pk=variant.product_id)


@dg_admin_required
def product_variant_delete(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    product_id = variant.product_id
    if request.method == "POST":
        colour_name = variant.colour.name
        log_action(request, "Admin removed colour variant", f"{variant.product.name} — {colour_name}")
        variant.delete()
        messages.info(request, f"{colour_name} removed.")
    return redirect("dg_admin:product_edit", pk=product_id)


@dg_admin_required
def product_variant_image_delete(request, pk):
    image = get_object_or_404(VariantImage, pk=pk)
    product_id = image.variant.product_id
    if request.method == "POST":
        image.delete()
        messages.info(request, "Image removed.")
    return redirect("dg_admin:product_edit", pk=product_id)


@dg_admin_required
def product_variant_image_set_primary(request, pk):
    image = get_object_or_404(VariantImage, pk=pk)
    product_id = image.variant.product_id
    if request.method == "POST":
        image.is_primary = True
        image.save()  # VariantImage.save() clears is_primary on the variant's other images
        messages.success(request, "Primary image updated.")
    return redirect("dg_admin:product_edit", pk=product_id)


# ---------- Colours (the admin-managed palette used by product colour variants) ----------

@dg_admin_required
def colour_list(request):
    colours = Colour.objects.all()
    return render(request, "dg_admin/colour_list.html", {"colours": colours})


@dg_admin_required
def colour_add(request):
    if request.method == "POST":
        form = ColourForm(request.POST)
        if form.is_valid():
            colour = form.save()
            log_action(request, "Admin added colour", colour.name)
            messages.success(request, f"{colour.name} added.")
            return redirect("dg_admin:colour_list")
    else:
        form = ColourForm()
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": "Add Colour"})


@dg_admin_required
def colour_edit(request, pk):
    colour = get_object_or_404(Colour, pk=pk)
    if request.method == "POST":
        form = ColourForm(request.POST, instance=colour)
        if form.is_valid():
            form.save()
            log_action(request, "Admin updated colour", colour.name)
            messages.success(request, f"{colour.name} updated.")
            return redirect("dg_admin:colour_list")
    else:
        form = ColourForm(instance=colour)
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": f"Edit Colour — {colour.name}"})


@dg_admin_required
def colour_delete(request, pk):
    colour = get_object_or_404(Colour, pk=pk)
    if request.method == "POST":
        if colour.variants.exists():
            messages.error(request, f"Can't delete {colour.name} — it's used by {colour.variants.count()} product variant(s). Disable it instead.")
        else:
            name = colour.name
            colour.delete()
            log_action(request, "Admin deleted colour", name)
            messages.info(request, f"{name} deleted.")
    return redirect("dg_admin:colour_list")


@dg_admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        log_action(request, "Admin deleted product", product.name)
        product.delete()
        messages.info(request, "Product deleted.")
    return redirect("dg_admin:product_list")


# ---------- Categories ----------

@dg_admin_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, "dg_admin/category_list.html", {"categories": categories})


@dg_admin_required
def category_form(request, pk=None):
    category = get_object_or_404(Category, pk=pk) if pk else None
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            log_action(request, "Admin saved category", form.instance.name)
            messages.success(request, "Category saved.")
            return redirect("dg_admin:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": "Category"})


@dg_admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        log_action(request, "Admin deleted category", category.name)
        messages.info(request, "Category deleted.")
    return redirect("dg_admin:category_list")


# ---------- Delivery Management ----------

@dg_admin_required
def delivery_list(request):
    site = SiteSettings.load()
    if request.method == "POST" and request.POST.get("action") == "set_delivery_mode":
        mode = request.POST.get("delivery_mode")
        if mode in {"weight", "count", "product_state"}:
            site.delivery_mode = mode
            site.save(update_fields=["delivery_mode"])
            messages.success(request, "Delivery calculation mode updated.")
        return redirect("dg_admin:delivery_list")
    slabs = DeliveryWeightSlab.objects.all()
    products = Product.objects.all().order_by("name")
    return render(request, "dg_admin/delivery_list.html", {"slabs": slabs, "products": products, "delivery_mode": site.delivery_mode})


@dg_admin_required
def delivery_form(request, pk=None):
    slab = get_object_or_404(DeliveryWeightSlab, pk=pk) if pk else None
    if request.method == "POST":
        form = DeliveryWeightSlabForm(request.POST, instance=slab)
        if form.is_valid():
            obj = form.save()
            log_action(request, "Admin saved delivery weight slab", str(obj))
            messages.success(request, "Delivery slab saved.")
            return redirect("dg_admin:delivery_list")
    else:
        form = DeliveryWeightSlabForm(instance=slab)
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": "Delivery Weight Slab"})


@dg_admin_required
def delivery_delete(request, pk):
    slab = get_object_or_404(DeliveryWeightSlab, pk=pk)
    if request.method == "POST":
        log_action(request, "Admin deleted delivery weight slab", str(slab))
        slab.delete()
        messages.info(request, "Delivery slab deleted.")
    return redirect("dg_admin:delivery_list")


@dg_admin_required
def delivery_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delivery_enabled = request.POST.get("delivery_enabled") == "on"
        product.free_delivery = request.POST.get("free_delivery") == "on"
        product.first_item_delivery_charge = Decimal(request.POST.get("first_item_delivery_charge") or "0")
        product.additional_item_delivery_charge = Decimal(request.POST.get("additional_item_delivery_charge") or "0")
        product.save()
        log_action(request, "Admin updated product delivery", product.name)
        messages.success(request, "Product delivery settings updated.")
        return redirect("dg_admin:delivery_list")
    return render(request, "dg_admin/delivery_edit.html", {"product": product})


@dg_admin_required
def delivery_calculator(request):
    from site_settings.models import SiteSettings
    from orders.services.delivery import calculate_slab_delivery
    mode = SiteSettings.load().delivery_mode
    result = None
    if request.method == "POST" and mode == "count":
        try:
            test_count = max(0, int(request.POST.get("test_count") or 0))
        except ValueError:
            test_count = 0
        from orders.services.delivery import calculate_count_delivery
        charge, count, rule = calculate_count_delivery([(None, test_count)])
        result = {"mode": "count", "count": count, "rule": rule, "total": charge}
    elif request.method == "POST":
        product_ids = request.POST.getlist("product_id")
        quantities = request.POST.getlist("quantity")
        lines = []
        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty:
                continue
            product = Product.objects.filter(id=pid).first()
            if not product:
                continue
            qty = max(0, int(qty))
            if qty:
                lines.append((product, qty))
        charge, weight, slab = calculate_slab_delivery(lines)
        result = {"mode": "weight", "total": charge, "weight": weight, "slab": slab}
    products = Product.objects.filter(active=True)
    return render(request, "dg_admin/delivery_calculator.html", {"products": products, "result": result, "delivery_mode": mode})


# ---------- Orders ----------

@dg_admin_required
def order_list(request):
    orders = Order.objects.exclude(order_status="awaiting_payment")
    q = request.GET.get("q")
    status = request.GET.get("status")
    payment_status = request.GET.get("payment_status")
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) | Q(customer_name_snapshot__icontains=q)
            | Q(phone_snapshot__icontains=q) | Q(email_snapshot__icontains=q)
        )
    if status:
        orders = orders.filter(order_status=status)
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    paginator = Paginator(orders, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dg_admin/order_list.html", {
        "page_obj": page_obj, "q": q or "", "status": status or "", "payment_status": payment_status or "",
        "status_choices": Order.ADMIN_STATUS_CHOICES,
    })


@dg_admin_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == "POST":
        new_status = request.POST.get("order_status")
        expected_date = request.POST.get("expected_delivery_date")
        notes = request.POST.get("notes")
        if request.POST.get("action") == "refund_complete":
            order.refund_status = "completed"
            order.order_status = "cancelled"
            order.save(update_fields=["refund_status", "order_status", "updated_date"])
            log_action(request, "Admin marked refund completed", order.order_number)
            messages.success(request, "Refund marked completed.")
            return redirect("dg_admin:order_detail", order_number=order.order_number)
        if new_status:
            order.order_status = new_status
        if expected_date:
            order.expected_delivery_date = expected_date
        order.notes = notes or ""
        order.save()
        log_action(request, "Admin updated order status", order.order_number)
        messages.success(request, "Order updated.")
        return redirect("dg_admin:order_detail", order_number=order.order_number)
    return render(request, "dg_admin/order_detail.html", {"order": order, "status_choices": Order.ADMIN_STATUS_CHOICES})


# ---------- Payments ----------

@dg_admin_required
def payment_list(request):
    payments = Payment.objects.select_related("order").order_by("-submitted_at")
    return render(request, "dg_admin/payment_list.html", {"payments": payments})


@dg_admin_required
def payment_review(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            payment.order.payment_status = "received"
            payment.rejection_note = ""
            log_action(request, "Admin approved payment", payment.order.order_number)
        elif action == "reject":
            payment.order.payment_status = "rejected"
            payment.rejection_note = request.POST.get("rejection_note", "")
            log_action(request, "Admin rejected payment", payment.order.order_number)
        payment.reviewed_at = timezone.now()
        payment.save()
        payment.order.save()
        messages.success(request, "Payment reviewed.")
        return redirect("dg_admin:payment_list")
    return render(request, "dg_admin/payment_review.html", {"payment": payment})


# ---------- Customers ----------

@dg_admin_required
def customer_list(request):
    customers = User.objects.filter(is_staff=False)
    q = request.GET.get("q")
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
    paginator = Paginator(customers, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dg_admin/customer_list.html", {"page_obj": page_obj, "q": q or ""})


@dg_admin_required
def customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    orders = Order.objects.filter(user=customer).exclude(order_status="awaiting_payment")
    total_spent = orders.exclude(order_status="cancelled").aggregate(s=Sum("grand_total"))["s"] or Decimal("0.00")
    return render(request, "dg_admin/customer_detail.html", {
        "customer": customer, "orders": orders, "total_spent": total_spent,
    })


# ---------- Coupons ----------

@dg_admin_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request, "dg_admin/coupon_list.html", {"coupons": coupons})


@dg_admin_required
def coupon_form(request, pk=None):
    coupon = get_object_or_404(Coupon, pk=pk) if pk else None
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon saved.")
            return redirect("dg_admin:coupon_list")
    else:
        form = CouponForm(instance=coupon)
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": "Coupon"})


@dg_admin_required
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == "POST":
        coupon.delete()
        messages.info(request, "Coupon deleted.")
    return redirect("dg_admin:coupon_list")


# ---------- Generic CRUD factory for simple content models ----------

_SIMPLE_MODELS = {
    "hero": (HeroSlide, HeroSlideForm, "Hero Slide"),
    "stories": (Story, StoryForm, "Story"),
    "advertisements": (Advertisement, AdvertisementForm, "Advertisement"),
    "faq": (FAQ, FAQForm, "FAQ"),
    "offers": (Offer, OfferForm, "Offer"),
}


@dg_admin_required
def simple_list(request, kind):
    model, _, label = _SIMPLE_MODELS[kind]
    items = model.objects.all()
    return render(request, "dg_admin/simple_list.html", {"items": items, "kind": kind, "label": label})


@dg_admin_required
def simple_form(request, kind, pk=None):
    model, form_cls, label = _SIMPLE_MODELS[kind]
    instance = get_object_or_404(model, pk=pk) if pk else None
    if request.method == "POST":
        form = form_cls(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{label} saved.")
            return redirect("dg_admin:simple_list", kind=kind)
    else:
        form = form_cls(instance=instance)
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": label})


@dg_admin_required
def simple_delete(request, kind, pk):
    model, _, label = _SIMPLE_MODELS[kind]
    instance = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        instance.delete()
        messages.info(request, f"{label} deleted.")
    return redirect("dg_admin:simple_list", kind=kind)


# ---------- Customization ----------

@dg_admin_required
def customization_list(request):
    items = Customization.objects.select_related("product", "user").order_by("-created_date")
    return render(request, "dg_admin/customization_list.html", {"items": items})


# ---------- Hopy / Chat ----------

@dg_admin_required
def chat_list(request):
    conversations = ChatConversation.objects.order_by("-created_date")
    return render(request, "dg_admin/chat_list.html", {"conversations": conversations})


@dg_admin_required
def chat_detail(request, pk):
    conversation = get_object_or_404(ChatConversation, pk=pk)
    if request.method == "POST" and request.POST.get("action") == "delete":
        conversation.delete()
        messages.info(request, "Conversation deleted.")
        return redirect("dg_admin:chat_list")
    return render(request, "dg_admin/chat_detail.html", {"conversation": conversation})


# ---------- Storage Manager ----------

# Maps the top-level media subfolder each upload path uses to a friendly category label.
# Anything not matched falls into "Other".
_STORAGE_CATEGORIES = [
    ("products/gallery", "Product Gallery Images"),
    ("products", "Product Images"),
    ("hero", "Hero Images"),
    ("stories", "Story Images"),
    ("categories", "Category Images"),
    ("payments/proofs", "Payment Proofs"),
    ("customization/reference", "Customization Reference Images"),
    ("customization/output", "Customization Output Images"),
    ("chat", "Chat Images"),
    ("ads", "Advertisement Images"),
    ("offers", "Offer Images"),
    ("profiles", "Profile Images"),
    ("site", "Site Branding (Logo/Favicon/QR)"),
]


def _categorize_storage_path(rel_path):
    normalized = rel_path.replace("\\", "/")
    for prefix, label in _STORAGE_CATEGORIES:
        if normalized.startswith(prefix + "/"):
            return label
    return "Other"


@dg_admin_required
def storage_manager(request):
    import os
    from django.conf import settings as dj_settings
    media_root = dj_settings.MEDIA_ROOT
    selected_category = request.GET.get("category", "")

    all_files = []
    if os.path.isdir(media_root):
        for root, _, filenames in os.walk(media_root):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, media_root)
                category = _categorize_storage_path(rel)
                all_files.append({"path": rel, "size_kb": round(os.path.getsize(full) / 1024, 1), "category": category})

    # Category summary: name -> (count, total_kb)
    summary = {}
    for f in all_files:
        c = summary.setdefault(f["category"], {"count": 0, "total_kb": 0.0})
        c["count"] += 1
        c["total_kb"] += f["size_kb"]
    summary_rows = sorted(
        [{"category": k, "count": v["count"], "total_kb": round(v["total_kb"], 1)} for k, v in summary.items()],
        key=lambda r: -r["total_kb"],
    )

    files = [f for f in all_files if not selected_category or f["category"] == selected_category]
    files.sort(key=lambda f: f["path"])

    return render(request, "dg_admin/storage_manager.html", {
        "files": files, "summary_rows": summary_rows, "selected_category": selected_category,
        "total_files": len(all_files), "total_kb": round(sum(f["size_kb"] for f in all_files), 1),
    })


@dg_admin_required
def storage_delete(request):
    import os
    from django.conf import settings as dj_settings
    return_category = ""
    if request.method == "POST":
        selected = request.POST.getlist("selected")
        return_category = request.POST.get("return_category", "")
        for rel in selected:
            full = os.path.join(dj_settings.MEDIA_ROOT, rel)
            if os.path.isfile(full) and os.path.commonpath([full, str(dj_settings.MEDIA_ROOT)]) == str(dj_settings.MEDIA_ROOT):
                os.remove(full)
        log_action(request, "Admin deleted media files", f"{len(selected)} file(s)")
        messages.info(request, "Selected files deleted.")
    if return_category:
        from django.urls import reverse
        from urllib.parse import urlencode
        return redirect(reverse("dg_admin:storage_manager") + "?" + urlencode({"category": return_category}))
    return redirect("dg_admin:storage_manager")


# ---------- Reports ----------

_DATE_PRESETS = ["today", "yesterday", "7d", "30d", "this_month", "last_month", "this_year"]


def _resolve_date_range(request):
    """Returns (start_date, end_date, label) as date objects (inclusive), or (None, None, label)
    for 'all time' when no filter is given. Supports presets and a custom range."""
    preset = request.GET.get("range", "")
    today = timezone.localdate()

    if preset == "today":
        return today, today, "Today"
    if preset == "yesterday":
        d = today - timezone.timedelta(days=1)
        return d, d, "Yesterday"
    if preset == "7d":
        return today - timezone.timedelta(days=6), today, "Last 7 Days"
    if preset == "30d":
        return today - timezone.timedelta(days=29), today, "Last 30 Days"
    if preset == "this_month":
        return today.replace(day=1), today, "This Month"
    if preset == "last_month":
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timezone.timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end, "Last Month"
    if preset == "this_year":
        return today.replace(month=1, day=1), today, "This Year"
    if preset == "custom":
        start_str = request.GET.get("start_date")
        end_str = request.GET.get("end_date")
        if start_str and end_str:
            try:
                start = timezone.datetime.strptime(start_str, "%Y-%m-%d").date()
                end = timezone.datetime.strptime(end_str, "%Y-%m-%d").date()
                return start, end, f"{start_str} to {end_str}"
            except ValueError:
                pass
    return None, None, "All Time"


@dg_admin_required
def reports(request):
    orders = Order.objects.exclude(order_status__in=["cancelled", "awaiting_payment"])
    products_filter = request.GET.get("product")
    category_filter = request.GET.get("category")
    order_status_filter = request.GET.get("order_status")
    payment_status_filter = request.GET.get("payment_status")

    start_date, end_date, range_label = _resolve_date_range(request)
    if start_date and end_date:
        orders = orders.filter(created_date__date__gte=start_date, created_date__date__lte=end_date)
    if products_filter:
        orders = orders.filter(items__product_id=products_filter).distinct()
    if category_filter:
        orders = orders.filter(items__product__category_id=category_filter).distinct()
    if order_status_filter:
        orders = orders.filter(order_status=order_status_filter)
    if payment_status_filter:
        orders = orders.filter(payment_status=payment_status_filter)

    totals = orders.aggregate(
        revenue=Sum("grand_total"), discount=Sum("discount"), delivery=Sum("delivery_charge"), count=Count("id"),
    )
    order_count = totals["count"] or 0
    avg_order_value = (totals["revenue"] / order_count) if order_count else Decimal("0.00")

    product_breakdown = (
        OrderItem.objects.filter(order__in=orders)
        .values("product__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("subtotal"))
        .order_by("-revenue")[:15]
    )
    category_breakdown = (
        OrderItem.objects.filter(order__in=orders, product__category__isnull=False)
        .values("product__category__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("subtotal"))
        .order_by("-revenue")[:15]
    )

    return render(request, "dg_admin/reports.html", {
        "totals": totals, "avg_order_value": avg_order_value,
        "product_breakdown": product_breakdown, "category_breakdown": category_breakdown,
        "range_label": range_label, "current_range": request.GET.get("range", ""),
        "start_date": request.GET.get("start_date", ""), "end_date": request.GET.get("end_date", ""),
        "all_products": Product.objects.all(), "all_categories": Category.objects.all(),
        "status_choices": Order.ADMIN_STATUS_CHOICES, "payment_status_choices": Order.PAYMENT_STATUS_CHOICES,
        "selected_product": products_filter or "", "selected_category": category_filter or "",
        "selected_order_status": order_status_filter or "", "selected_payment_status": payment_status_filter or "",
    })


# ---------- Site Settings ----------

@dg_admin_required
def site_settings_dashboard(request):
    """Landing page for Site Settings: a card-based hub only. Each card opens its own full page."""
    cards = [
        {"title": "Branding & Business", "desc": "Store name, logo, WhatsApp/contact and business identity.", "url": reverse("dg_admin:site_settings_section", args=["business"])},
        {"title": "Global Theme", "desc": "Colours, typography and button tokens used across every page.", "url": reverse("dg_admin:site_settings_section", args=["global-theme"])},
        {"title": "Page Themes", "desc": "Per-page overrides that inherit from the global theme.", "url": reverse("dg_admin:site_settings_section", args=["page-theme"])},
        {"title": "Assets & Illustrations", "desc": "Delivery vehicle, empty states, success and other SVG assets.", "url": reverse("dg_admin:site_settings_section", args=["assets"])},
        {"title": "Animations", "desc": "Global motion controls with reduced-motion support.", "url": reverse("dg_admin:site_settings_section", args=["animation"])},
        {"title": "Payment", "desc": "UPI ID, QR code and payment verification settings.", "url": reverse("dg_admin:payment_list")},
        {"title": "Delivery", "desc": "Choose weight-based or product-count delivery and manage slabs.", "url": reverse("dg_admin:delivery_list")},
        {"title": "WhatsApp & Customization", "desc": "WhatsApp destination, default message and customization flow.", "url": reverse("dg_admin:customization_list")},
        {"title": "Chatbot", "desc": "Hopy chat conversations and assistant behaviour.", "url": reverse("dg_admin:chat_list")},
    ]
    return render(request, "dg_admin/site_settings_dashboard.html", {"cards": cards})


@dg_admin_required
def site_settings_view(request):
    site = SiteSettings.load()
    theme = ThemeSettings.load()
    animation = AnimationSettings.load()
    selected_page = request.GET.get("page", "home")
    if selected_page not in dict(PAGE_KEYS):
        selected_page = "home"
    page_theme, _ = PageTheme.objects.get_or_create(page_key=selected_page)
    asset_key = request.GET.get("asset", "delivery_bike")
    valid_assets = dict(AssetSetting.KEY_CHOICES)
    if asset_key not in valid_assets:
        asset_key = "delivery_bike"
    asset, _ = AssetSetting.objects.get_or_create(key=asset_key)

    if request.method == "POST":
        section = request.POST.get("section")
        if section == "site":
            form = SiteSettingsForm(request.POST, request.FILES, instance=site)
            if form.is_valid():
                form.save(); log_action(request, "Admin updated site/business settings", site.store_name); messages.success(request, "Site and business settings saved.")
                return redirect("dg_admin:site_settings")
        elif section == "theme":
            form = ThemeSettingsForm(request.POST, instance=theme)
            if form.is_valid():
                form.save(); log_action(request, "Admin updated global theme", "ThemeSettings"); messages.success(request, "Global theme saved.")
                return redirect("dg_admin:site_settings")
        elif section == "page_theme":
            form = PageThemeForm(request.POST, instance=page_theme)
            if form.is_valid():
                form.save(); messages.success(request, "Page theme override saved.")
                return redirect(f"/admin/site-settings/?page={selected_page}")
        elif section == "animation":
            form = AnimationSettingsForm(request.POST, instance=animation)
            if form.is_valid():
                form.save(); messages.success(request, "Animation settings saved.")
                return redirect("dg_admin:site_settings")
        elif section == "asset":
            form = AssetSettingForm(request.POST, request.FILES, instance=asset)
            if form.is_valid():
                form.save(); messages.success(request, "Asset setting saved.")
                return redirect(f"/admin/site-settings/?asset={asset_key}")

    return render(request, "dg_admin/site_settings.html", {
        "site_form": SiteSettingsForm(instance=site), "theme_form": ThemeSettingsForm(instance=theme),
        "page_form": PageThemeForm(instance=page_theme), "animation_form": AnimationSettingsForm(instance=animation),
        "asset_form": AssetSettingForm(instance=asset), "page_keys": PAGE_KEYS, "selected_page": selected_page,
        "asset_choices": AssetSetting.KEY_CHOICES, "selected_asset": asset_key, "site": site, "asset": asset,
    })



@dg_admin_required
def site_settings_section(request, section):
    """Single-section Site Settings pages. Keeps the existing backend while avoiding a crowded settings dashboard."""
    allowed = {"business", "global-theme", "page-theme", "assets", "animation"}
    if section not in allowed:
        return redirect("dg_admin:site_settings_section", section="business")
    site = SiteSettings.load(); theme = ThemeSettings.load(); animation = AnimationSettings.load()
    selected_page = request.GET.get("page", "home")
    if selected_page not in dict(PAGE_KEYS): selected_page = "home"
    page_theme, _ = PageTheme.objects.get_or_create(page_key=selected_page)
    asset_key = request.GET.get("asset", "delivery_bike")
    if asset_key not in dict(AssetSetting.KEY_CHOICES): asset_key = "delivery_bike"
    asset, _ = AssetSetting.objects.get_or_create(key=asset_key)
    if request.method == "POST":
        target = request.POST.get("section", section)
        if target == "site":
            form = SiteSettingsForm(request.POST, request.FILES, instance=site)
            if form.is_valid(): form.save(); messages.success(request, "Business settings saved."); return redirect("dg_admin:site_settings_section", section="business")
        if target == "theme":
            form = ThemeSettingsForm(request.POST, instance=theme)
            if form.is_valid(): form.save(); messages.success(request, "Global theme saved."); return redirect("dg_admin:site_settings_section", section="global-theme")
        if target == "page_theme":
            form = PageThemeForm(request.POST, instance=page_theme)
            if form.is_valid(): form.save(); messages.success(request, "Page theme saved."); return redirect("dg_admin:site_settings_section", section="page-theme")
        if target == "animation":
            form = AnimationSettingsForm(request.POST, instance=animation)
            if form.is_valid(): form.save(); messages.success(request, "Animation settings saved."); return redirect("dg_admin:site_settings_section", section="animation")
        if target == "asset":
            form = AssetSettingForm(request.POST, request.FILES, instance=asset)
            if form.is_valid(): form.save(); messages.success(request, "Asset setting saved."); return redirect("dg_admin:site_settings_section", section="assets")
    forms_ctx={"site_form":SiteSettingsForm(instance=site),"theme_form":ThemeSettingsForm(instance=theme),"page_form":PageThemeForm(instance=page_theme),"animation_form":AnimationSettingsForm(instance=animation),"asset_form":AssetSettingForm(instance=asset)}
    return render(request,"dg_admin/site_settings_section.html",dict(forms_ctx,section=section,site=site,asset=asset,page_keys=PAGE_KEYS,selected_page=selected_page,asset_choices=AssetSetting.KEY_CHOICES,selected_asset=asset_key))

@dg_admin_required
def product_gallery_set_primary(request, pk):
    from products.models import ProductImage
    image = get_object_or_404(ProductImage, pk=pk)
    if request.method == "POST":
        product = image.product
        product.main_image = image.image
        product.save(update_fields=["main_image", "updated_date"])
        messages.success(request, "Primary product image updated.")
    return redirect("dg_admin:product_edit", pk=image.product_id)


@dg_admin_required
def product_gallery_reorder(request, product_id):
    from products.models import ProductImage
    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        for image in product.images.all():
            try:
                order = max(0, int(request.POST.get(f"order_{image.id}", image.display_order)))
            except (TypeError, ValueError):
                order = image.display_order
            if image.display_order != order:
                image.display_order = order
                image.save(update_fields=["display_order"])
        messages.success(request, "Product gallery order updated.")
    return redirect("dg_admin:product_edit", pk=product.id)


@dg_admin_required
def reset_page_theme(request, page_key):
    page = get_object_or_404(PageTheme, page_key=page_key)
    if request.method == "POST":
        for field in ["background","surface","text","muted_text","heading","accent","button","button_text","button_hover","border","input_background","input_text","card","header","footer","search_background"]:
            setattr(page, field, "")
        page.save(); messages.success(request, "Page theme reset to global defaults.")
    return redirect(f"/admin/site-settings/?page={page_key}#page-theme")


@dg_admin_required
def reset_asset(request, key):
    asset = get_object_or_404(AssetSetting, key=key)
    if request.method == "POST":
        asset.asset = None; asset.enabled = True; asset.save(update_fields=["asset", "enabled"]); messages.success(request, "Asset reset. The safe built-in fallback will be used where available.")
    return redirect(f"/admin/site-settings/?asset={key}#assets")


@dg_admin_required
def delivery_count_list(request):
    rules = DeliveryCountRule.objects.all()
    return render(request, "dg_admin/delivery_count_list.html", {"rules": rules})


@dg_admin_required
def delivery_count_form(request, pk=None):
    rule = get_object_or_404(DeliveryCountRule, pk=pk) if pk else None
    if request.method == "POST":
        form = DeliveryCountRuleForm(request.POST, instance=rule)
        if form.is_valid():
            obj = form.save(); log_action(request, "Admin saved product-count delivery rule", str(obj)); messages.success(request, "Product-count delivery rule saved.")
            return redirect("dg_admin:delivery_count_list")
    else:
        form = DeliveryCountRuleForm(instance=rule)
    return render(request, "dg_admin/generic_form.html", {"form": form, "title": "Product Count Delivery Rule"})


@dg_admin_required
def delivery_count_delete(request, pk):
    rule = get_object_or_404(DeliveryCountRule, pk=pk)
    if request.method == "POST":
        rule.delete(); messages.info(request, "Product-count delivery rule deleted.")
    return redirect("dg_admin:delivery_count_list")


@dg_admin_required
def product_gallery_delete(request, pk):
    from products.models import ProductImage
    image = get_object_or_404(ProductImage, pk=pk)
    product_id = image.product_id
    if request.method == "POST":
        image.delete(); messages.info(request, "Product gallery image removed.")
    return redirect("dg_admin:product_edit", pk=product_id)


# ---------- Admin Users ----------

@dg_admin_required
def admin_users(request):
    staff = User.objects.filter(is_staff=True).order_by("-is_superuser", "name")
    return render(request, "dg_admin/admin_users.html", {"staff": staff, "can_manage": request.user.is_superuser})


@dg_superuser_required
def admin_user_form(request, pk=None):
    from .forms import AdminUserForm
    instance = get_object_or_404(User, pk=pk, is_staff=True) if pk else None
    is_new = instance is None

    if request.method == "POST":
        form = AdminUserForm(request.POST, instance=instance)
        if is_new and not request.POST.get("password"):
            form.add_error("password", "A password is required for a new admin account.")
        if form.is_valid():
            user = form.save()
            log_action(request, "Admin created admin user" if is_new else "Admin updated admin user", user.email)
            messages.success(request, "Admin user saved.")
            return redirect("dg_admin:admin_users")
    else:
        form = AdminUserForm(instance=instance)

    return render(request, "dg_admin/generic_form.html", {
        "form": form, "title": "New Admin User" if is_new else f"Edit Admin User — {instance.name}",
    })


@dg_superuser_required
def admin_user_toggle_active(request, pk):
    target = get_object_or_404(User, pk=pk, is_staff=True)
    if request.method == "POST":
        if target == request.user:
            messages.error(request, "You can't deactivate your own account.")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            log_action(request, f"Admin {'activated' if target.is_active else 'deactivated'} admin user", target.email)
            messages.success(request, f"{target.name} is now {'active' if target.is_active else 'inactive'}.")
    return redirect("dg_admin:admin_users")


@dg_superuser_required
def admin_user_remove_access(request, pk):
    """Revokes staff/admin access without deleting the underlying account or its order history."""
    target = get_object_or_404(User, pk=pk, is_staff=True)
    if request.method == "POST":
        if target == request.user:
            messages.error(request, "You can't remove your own admin access.")
        else:
            target.is_staff = False
            target.is_superuser = False
            target.save(update_fields=["is_staff", "is_superuser"])
            log_action(request, "Admin removed admin access from user", target.email)
            messages.info(request, f"Admin access removed for {target.name}.")
    return redirect("dg_admin:admin_users")


# ---------- Audit Log ----------

@dg_admin_required
def audit_log(request):
    logs = AuditLog.objects.all()[:200]
    return render(request, "dg_admin/audit_log.html", {"logs": logs})


# ---------- Global Search ----------

@dg_admin_required
def global_search(request):
    q = request.GET.get("q", "").strip()
    results = {"orders": [], "products": [], "customers": []}
    if q:
        results["orders"] = Order.objects.exclude(order_status="awaiting_payment").filter(
            Q(order_number__icontains=q) | Q(customer_name_snapshot__icontains=q)
        )[:10]
        results["products"] = Product.objects.filter(Q(name__icontains=q) | Q(sku__icontains=q))[:10]
        results["customers"] = User.objects.filter(
            Q(name__icontains=q) | Q(email__icontains=q), is_staff=False
        )[:10]
    return render(request, "dg_admin/global_search.html", {"q": q, "results": results})
