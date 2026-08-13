from django.shortcuts import render

from advertisements.models import Advertisement
from offers.models import Offer
from coupons.models import Coupon
from django.utils import timezone
import random
from products.models import Product
from categories.models import Category
from .models import SiteSettings, StorySlide, Banner


def home(request):
    story_slides = list(StorySlide.objects.filter(active=True))
    banners = list(Banner.current())
    random.shuffle(story_slides)
    random.shuffle(banners)
    featured_products = Product.objects.filter(active=True, featured=True)[:8]
    categories = Category.objects.filter(active=True)
    offers = Offer.visible_for(request.user)
    now = timezone.now()
    coupons = Coupon.objects.filter(active=True, start_date__lte=now, expiry_date__gte=now)[:6]
    homepage_ads = Advertisement.visible_for('homepage_banner', request.user)
    strip_ads = Advertisement.visible_for('promotional_strip', request.user)
    popup_ad = Advertisement.visible_for('homepage_banner', request.user).filter(full_screen_popup=True).first()

    return render(request, 'home.html', {
        'story_slides': story_slides,
        'banners': banners,
        'featured_products': featured_products,
        'categories': categories,
        'offers': offers,
        'coupons': coupons,
        'homepage_ads': homepage_ads,
        'strip_ads': strip_ads,
        'popup_ad': popup_ad,
    })


def about(request):
    settings_obj = SiteSettings.load()
    return render(request, 'about.html', {'site_settings': settings_obj})
