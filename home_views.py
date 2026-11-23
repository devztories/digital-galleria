import random
import re

from django.core.cache import cache
from django.shortcuts import render
from products.models import Product
from categories.models import Category
from site_settings.models import HeroSlide, Story, Advertisement


def _shuffled(qs, limit=None):
    """Random order on every page load, so every admin-supplied image gets its turn."""
    items = list(qs)
    random.shuffle(items)
    return items[:limit] if limit else items


def home_view(request):
    hero_slides = _shuffled(HeroSlide.objects.filter(active=True))
    stories = _shuffled(Story.objects.filter(active=True))
    categories = _shuffled(Category.objects.filter(active=True))
    # shuffle the whole pool first, THEN cut to 12, so different products surface each visit
    featured_products = _shuffled(Product.objects.filter(active=True, featured=True), 20)
    personal_products = _shuffled(Product.objects.filter(active=True, customizable=True), 20)
    advertisements = _shuffled(Advertisement.objects.filter(active=True))

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


def _client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (fwd.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")) or "unknown"


def _normalise_order_number(raw):
    """Accepts 'DG3001', 'dg 3001', '#DG3001' or just '3001'."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw or "").upper()
    if cleaned.isdigit():
        cleaned = "DG" + cleaned
    return cleaned[:20]


def about_view(request):
    """About page with a public 'Track any order' box.

    Anyone (no login) can enter an order ID and see the tracking STATUS of that
    order. Only status information is exposed - never the customer's name,
    phone, address, items' customization or payment proof. Lookups are
    throttled per visitor so order numbers cannot be scanned in bulk.
    """
    from orders.models import Order

    raw = (request.GET.get("order") or "").strip()
    ctx = {"track_query": raw, "track_order": None, "track_error": "", "track_stages": []}
    if raw:
        key = f"track-throttle:{_client_ip(request)}"
        hits = cache.get(key, 0)
        if hits >= 30:
            ctx["track_error"] = "Too many lookups. Please wait a minute and try again."
        else:
            cache.set(key, hits + 1, 60)
            number = _normalise_order_number(raw)
            order = Order.objects.filter(order_number=number).exclude(order_status="awaiting_payment").first() if number else None
            if order:
                ctx["track_order"] = order
                ctx["track_stages"] = order.status_progress()
                reached = sum(1 for _, done in ctx["track_stages"] if done)
                total = len(ctx["track_stages"])
                ctx["track_progress"] = round(max(reached - 1, 0) / (total - 1), 3) if total > 1 else 0
                ctx["track_item_count"] = sum(i.quantity for i in order.items.all())
            else:
                ctx["track_error"] = "We couldn't find an order with that ID. Please check it and try again."
    return render(request, "about.html", ctx)
