from django.contrib import admin
from .models import SiteSettings, HeroSlide, Story, Advertisement, FAQ, Offer, ThemeSettings, PageTheme, AssetSetting, AnimationSettings

admin.site.register([SiteSettings, HeroSlide, Story, Advertisement, FAQ, Offer, ThemeSettings, PageTheme, AssetSetting, AnimationSettings])
