from django.shortcuts import render
from products.models import Product
from categories.models import Category
from site_settings.models import HeroSlide, Story, Advertisement


def home_view(request):
    hero_slides = HeroSlide.objects.filter(active=True)
    stories = list(Story.objects.filter(active=True))
    import random
    random.shuffle(stories)  # automatic shuffle/reorder on page load
    categories = Category.objects.filter(active=True)
    featured_products = Product.objects.filter(active=True, featured=True)[:12]
    personal_products = Product.objects.filter(active=True, customizable=True)[:12]
    advertisements = Advertisement.objects.filter(active=True)

    return render(request, "home.html", {
        "hero_slides": hero_slides,
        "stories": stories,
        "categories": categories,
        "featured_products": featured_products,
        "personal_products": personal_products,
        "advertisements": advertisements,
    })


def policy_view(request, page):
    return render(request, f"policies/{page}.html")
