from django.shortcuts import render, get_object_or_404
from .models import Category
from products.models import Product


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, active=True)
    products = Product.objects.filter(category=category, active=True)
    return render(request, 'categories/category_detail.html', {'category': category, 'products': products})
