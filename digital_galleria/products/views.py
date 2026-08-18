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
    product = get_object_or_404(Product, slug=slug, active=True)
    related = Product.objects.filter(category=product.category, active=True).exclude(pk=product.pk)[:6]
    return render(request, "products/detail.html", {"product": product, "related": related})


def search_suggestions(request):
    """Typo-tolerant search suggestions (JSON), backed by services.search.search_products."""
    from django.http import JsonResponse
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    matches = search_products(q, limit=8)
    results = [{"name": p.name, "slug": p.slug} for p in matches]
    return JsonResponse({"results": results})
