from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from .models import Product
from categories.models import Category
from .services.search import search_products


def product_list(request):
    products = Product.objects.filter(active=True)
    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)
    query = request.GET.get("q")
    if query:
        exact = products.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query)
        )
        if exact.exists():
            products = exact
        else:
            # No exact/substring hits — fall back to typo-tolerant fuzzy matching.
            # search_products returns a ranked list (not a queryset), so we paginate that directly.
            products = search_products(query, queryset=Product.objects.filter(active=True), limit=48)
    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))
    categories = Category.objects.filter(active=True)
    return render(request, "products/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "query": query or "",
        "category_slug": category_slug or "",
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("images", "variants__colour", "variants__images"),
        slug=slug, active=True,
    )
    related = Product.objects.filter(category=product.category, active=True).exclude(pk=product.pk)[:6]

    variants = list(product.active_variants())
    selected_variant = None
    if variants:
        requested_colour = request.GET.get("colour", "")
        selected_variant = product.get_variant_by_colour_slug(requested_colour) if requested_colour else None
        if not selected_variant:
            # Invalid/missing colour param gracefully falls back to the first active variant.
            selected_variant = variants[0]

    return render(request, "products/detail.html", {
        "product": product,
        "related": related,
        "variants": variants,
        "selected_variant": selected_variant,
        # Computed explicitly here (not in the template) — a None variant
        # combined with Django's silent-attribute-failure-on-None previously
        # caused non-variant products to show "out of stock" incorrectly.
        "display_in_stock": selected_variant.in_stock if selected_variant else product.in_stock,
        "display_stock": selected_variant.stock if selected_variant else product.stock,
    })


def variant_detail(request, slug):
    """AJAX endpoint: returns JSON for a given colour so the storefront can
    swap gallery/price/stock/SKU without a full page reload."""
    from django.http import JsonResponse
    product = get_object_or_404(Product, slug=slug, active=True)
    colour_slug = request.GET.get("colour", "")
    variant = product.get_variant_by_colour_slug(colour_slug)
    if not variant:
        return JsonResponse({"error": "not_found"}, status=404)
    images = [img.image.url for img in variant.images.all()]
    return JsonResponse({
        "variant_id": variant.id,
        "colour": variant.colour.name,
        "colour_hex": variant.colour.hex_code,
        "sku": variant.sku,
        "price": str(variant.effective_price),
        "base_price": str(variant.base_price),
        "discount_percent": (
            round((1 - (variant.discount_price / variant.base_price)) * 100)
            if variant.discount_price and variant.base_price else 0
        ),
        "stock": variant.stock,
        "in_stock": variant.in_stock,
        "images": images,
    })


def search_suggestions(request):
    """Typo-tolerant search suggestions (JSON), backed by services.search.search_products."""
    from django.http import JsonResponse
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    matches = search_products(q, limit=8)
    results = [{"name": p.name, "slug": p.slug} for p in matches]
    return JsonResponse({"results": results})
