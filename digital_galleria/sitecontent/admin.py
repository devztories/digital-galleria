from django.contrib import admin
from .models import SiteSettings, StorySlide, Banner


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Brand', {'fields': ('brand_name', 'tagline', 'logo', 'favicon')}),
        ('Hero Section', {'fields': ('hero_heading', 'hero_subheading', 'hero_image', 'hero_button_text', 'hero_button_url')}),
        ('About Section', {'fields': ('about_heading', 'about_description', 'about_image', 'about_mission', 'about_values')}),
        ('Social & Contact', {'fields': ('whatsapp_url', 'instagram_url', 'facebook_url', 'contact_email', 'contact_phone', 'address', 'footer_text')}),
        ('Payments', {'fields': ('upi_id', 'qr_code', 'payment_instructions')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(StorySlide)
class StorySlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'display_order', 'duration_seconds')
    list_editable = ('display_order', 'active', 'duration_seconds')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'display_order', 'start_date', 'end_date')
    list_editable = ('display_order', 'active')
