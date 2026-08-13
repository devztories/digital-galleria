from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from categories.models import Category
from .models import Product


def product_list(request):
    products = Product.objects.filter(active=True).select_related('category')
    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(keywords__icontains=query) | Q(category__name__icontains=query)
        )

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.filter(active=True)
    return render(request, 'products/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'active_category': category_slug,
        'query': query,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    related = Product.objects.filter(category=product.category, active=True).exclude(pk=product.pk)[:4]
    return render(request, 'products/product_detail.html', {'product': product, 'related': related})


def search_suggestions(request):
    """AJAX live-search endpoint. Returns lightweight JSON suggestions."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    products = Product.objects.filter(active=True).filter(
        Q(name__icontains=query) | Q(category__name__icontains=query) |
        Q(description__icontains=query) | Q(keywords__icontains=query)
    ).select_related('category')[:8]

    results = [{
        'name': p.name,
        'category': p.category.name,
        'url': p.get_absolute_url(),
        'price': str(p.price),
        'image': p.main_image.url if p.main_image else '',
    } for p in products]

    return JsonResponse({'results': results})
