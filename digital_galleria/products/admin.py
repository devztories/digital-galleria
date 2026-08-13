from django.contrib import admin
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'delivery_charge', 'stock', 'active', 'featured', 'customizable')
    list_filter = ('category', 'active', 'featured', 'customizable')
    search_fields = ('name', 'keywords', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'delivery_charge', 'stock', 'active', 'featured')
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'short_description', 'description', 'keywords')}),
        ('Pricing', {'fields': ('price', 'original_price', 'discount_percent', 'delivery_charge')}),
        ('Inventory & Visibility', {'fields': ('stock', 'active', 'featured')}),
        ('Customization', {'fields': ('customizable', 'max_custom_images')}),
        ('Images', {'fields': ('main_image',)}),
    )
