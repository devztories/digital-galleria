from django.shortcuts import render, get_object_or_404
from .models import Category
from products.models import Product


def category_list(request):
    categories = Category.objects.filter(active=True)
    return render(request, "categories/list.html", {"categories": categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, active=True)
    products = Product.objects.filter(category=category, active=True)
    return render(request, "categories/detail.html", {"category": category, "products": products})
