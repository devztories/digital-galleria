from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductImage, Colour, ProductVariant, VariantImage


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Lets one <input> accept several files at once (Django 5 built-in
    ClearableFileInput.allow_multiple_selected support — no extra package)."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ProductImageInline(admin.TabularInline):
    """Legacy gallery — kept for non-variant products / backward compatibility."""
    model = ProductImage
    extra = 1


class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1
    fields = ("image", "preview", "display_order", "is_primary")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;">', obj.image.url)
        return "—"
    preview.short_description = "Preview"


@admin.register(Colour)
class ColourAdmin(admin.ModelAdmin):
    list_display = ("name", "swatch", "hex_code", "active", "display_order")
    list_editable = ("display_order", "active")
    search_fields = ("name",)
    ordering = ("display_order", "name")

    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:18px;height:18px;border-radius:50%;'
            'border:1px solid #ccc;background:{}"></span>', obj.hex_code
        )
    swatch.short_description = "Colour"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "colour", "sku", "stock", "price_display", "active", "image_count")
    list_filter = ("active", "colour")
    search_fields = ("product__name", "sku", "colour__name")
    autocomplete_fields = ("product", "colour")
    inlines = [VariantImageInline]
    fieldsets = (
        ("Variant", {"fields": ("product", "colour", "sku", "active", "display_order")}),
        ("Inventory & Pricing", {"fields": ("stock", "price", "discount_price")}),
    )

    def price_display(self, obj):
        return f"₹{obj.effective_price}"
    price_display.short_description = "Effective Price"

    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = "Images"


class ProductVariantInlineForm(forms.ModelForm):
    # Not a model field — its uploaded files are picked up in
    # ProductAdmin.save_formset() and turned into VariantImage rows for this
    # variant, all in the SAME save as creating the product/colour itself.
    new_images = MultipleFileField(
        required=False,
        help_text="Upload one or more images for this colour — saved together with the product.",
    )

    class Meta:
        model = ProductVariant
        fields = "__all__"


class ProductVariantInline(admin.TabularInline):
    """Add/edit colour variants AND upload each colour's images directly on
    the Product page — no separate 'save variant first' step required."""
    model = ProductVariant
    form = ProductVariantInlineForm
    extra = 1
    fields = ("colour", "sku", "stock", "price", "discount_price", "active", "new_images", "existing_images")
    readonly_fields = ("existing_images",)
    autocomplete_fields = ("colour",)
    show_change_link = True

    def existing_images(self, obj):
        if not obj or not obj.pk:
            return "Will be uploaded on save"
        thumbs = "".join(
            format_html('<img src="{}" style="height:40px;border-radius:4px;margin-right:3px;">', img.image.url)
            for img in obj.images.all()[:6]
        )
        return format_html('{} <a href="/admin/products/productvariant/{}/change/">Manage ({})</a>', thumbs, obj.pk, obj.images.count())
    existing_images.short_description = "Current Images"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "discount_price", "stock", "colour_count", "weight", "weight_unit", "active")
    search_fields = ("name", "sku")
    fieldsets = (
        ("Product Information", {"fields": ("name", "slug", "description", "brand", "category", "sku", "active")}),
        ("Pricing", {"fields": ("price", "discount_price")}),
        ("Inventory", {"fields": ("stock", "main_image", "specifications", "featured", "bestseller")}),
        ("Customization", {"fields": ("customizable", "max_customization_images")}),
        ("Delivery", {"fields": ("weight", "weight_unit", "delivery_enabled", "free_delivery",
                                   "first_item_delivery_charge", "additional_item_delivery_charge")}),
    )
    inlines = [ProductVariantInline, ProductImageInline]

    def colour_count(self, obj):
        return obj.variants.filter(active=True).count()
    colour_count.short_description = "Colours"

    def save_formset(self, request, form, formset, change):
        """After the normal inline save, pick up each ProductVariant row's
        'new_images' multi-upload field and create VariantImage rows for it —
        so colours + their image galleries save together on one click."""
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj in instances:
            obj.save()
        formset.save_m2m()

        if formset.model is ProductVariant:
            for inline_form in formset.forms:
                if inline_form.cleaned_data.get("DELETE"):
                    continue
                files = inline_form.cleaned_data.get("new_images")
                variant = inline_form.instance
                if files and variant.pk:
                    start_order = variant.images.count()
                    for idx, f in enumerate(files):
                        VariantImage.objects.create(variant=variant, image=f, display_order=start_order + idx)
