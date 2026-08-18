from django import forms
import re
from accounts.models import User
from products.models import Product, ProductImage
from categories.models import Category
from coupons.models import Coupon
from site_settings.models import SiteSettings, HeroSlide, Story, Advertisement, FAQ, Offer, ThemeSettings, PageTheme, AssetSetting, AnimationSettings
from orders.models import DeliveryWeightSlab, DeliveryCountRule


class AdminUserForm(forms.ModelForm):
    """Create/edit a staff account. Password is optional on edit (leave blank to keep it unchanged)."""
    password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        help_text="4-8 characters. Leave blank when editing to keep the current password.",
    )

    class Meta:
        model = User
        fields = ["name", "email", "phone", "is_active", "is_superuser"]

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        if pwd and (len(pwd) < 4 or len(pwd) > 8):
            raise forms.ValidationError("Password must be between 4 and 8 characters.")
        return pwd

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # admin-users are always staff by definition of being managed here
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        elif not user.pk:
            # Creating a new admin without a password is not allowed — enforced in the view,
            # but guard here too in case save() is ever called directly.
            raise ValueError("A password is required when creating a new admin user.")
        if commit:
            user.save()
        return user



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "description", "brand", "category", "sku", "price", "discount_price", "stock",
            "main_image", "specifications", "featured", "bestseller", "customizable",
            "max_customization_images", "active",
            "weight", "weight_unit",
            "delivery_enabled", "free_delivery", "first_item_delivery_charge", "additional_item_delivery_charge",
        ]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "image", "display_order", "active"]


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["code", "discount_type", "discount_value", "minimum_order", "maximum_discount",
                  "start_date", "expiry_date", "usage_limit", "per_user_limit", "active"]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expiry_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = "__all__"


class ThemeSettingsForm(forms.ModelForm):
    class Meta:
        model = ThemeSettings
        exclude = []
        widgets = {
            field: forms.TextInput(attrs={"type": "color", "class": "color-input"})
            for field in ["background", "surface", "surface_alt", "text", "muted_text", "heading", "accent", "button", "button_text", "button_hover", "border", "input_background", "input_text", "card", "header", "footer", "search_background", "chatbot_background", "chatbot_surface", "chatbot_text", "chatbot_accent", "success", "danger", "admin_background", "admin_surface", "light_background", "light_surface", "light_text", "light_muted_text", "light_border", "default_animation_color_1", "default_animation_color_2", "default_animation_color_3"]
        }


    def clean(self):
        cleaned = super().clean()
        fields = [k for k in cleaned if k in {"background","surface","surface_alt","text","muted_text","heading","accent","button","button_text","button_hover","border","input_background","input_text","card","header","footer","search_background","chatbot_background","chatbot_surface","chatbot_text","chatbot_accent","success","danger","admin_background","admin_surface","light_background","light_surface","light_text","light_muted_text","light_border","default_animation_color_1","default_animation_color_2","default_animation_color_3"}]
        for key in fields:
            value = (cleaned.get(key) or "").strip()
            if value and not re.fullmatch(r"#[0-9A-Fa-f]{3,8}", value):
                self.add_error(key, "Use a valid hex colour such as #111214.")
        return cleaned


class PageThemeForm(forms.ModelForm):
    class Meta:
        model = PageTheme
        exclude = ["page_key"]
        widgets = {
            field: forms.TextInput(attrs={"class": "theme-text-input", "placeholder": "Inherit global theme"})
            for field in ["background", "surface", "text", "muted_text", "heading", "accent", "button", "button_text", "button_hover", "border", "input_background", "input_text", "card", "header", "footer", "search_background"]
        }


    def clean(self):
        cleaned = super().clean()
        for key, value in cleaned.items():
            if value and not re.fullmatch(r"#[0-9A-Fa-f]{3,8}", value.strip()):
                self.add_error(key, "Use a valid hex colour or leave blank to inherit.")
        return cleaned


class AssetSettingForm(forms.ModelForm):
    class Meta:
        model = AssetSetting
        fields = ["key", "asset", "enabled", "alt_text"]

    def clean_asset(self):
        asset = self.cleaned_data.get("asset")
        if not asset:
            return asset
        name = (asset.name or "").lower()
        if getattr(asset, "size", 0) > 10 * 1024 * 1024:
            raise forms.ValidationError("Asset files must be 10 MB or smaller.")
        allowed = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
        if not any(name.endswith(ext) for ext in allowed):
            raise forms.ValidationError("Use an image asset such as SVG, PNG, JPG, JPEG, WEBP or GIF.")
        if name.endswith(".svg"):
            try:
                raw = asset.read().decode("utf-8", errors="ignore")
                asset.seek(0)
            except Exception as exc:
                raise forms.ValidationError("The SVG file could not be read safely.") from exc
            lowered = raw.lower()
            if "<script" in lowered or "javascript:" in lowered or "onload=" in lowered or "onclick=" in lowered or "onerror=" in lowered:
                raise forms.ValidationError("This SVG contains unsafe script or event-handler content.")
        return asset


class AnimationSettingsForm(forms.ModelForm):
    class Meta:
        model = AnimationSettings
        exclude = ["key"]


class DeliveryCountRuleForm(forms.ModelForm):
    class Meta:
        model = DeliveryCountRule
        fields = ["min_items", "max_items", "charge", "is_active", "priority"]
        widgets = {
            "min_items": forms.NumberInput(attrs={"min": "1"}),
            "max_items": forms.NumberInput(attrs={"min": "1"}),
            "charge": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        self.instance.min_items = cleaned.get("min_items") or 0
        self.instance.max_items = cleaned.get("max_items")
        self.instance.charge = cleaned.get("charge") or 0
        self.instance.is_active = cleaned.get("is_active", True)
        self.instance.priority = cleaned.get("priority") or 0
        self.instance.clean()
        return cleaned


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = ["image", "title", "subtitle", "link", "display_order", "duration_ms", "active"]


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ["image", "duration_ms", "display_order", "active"]


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ["title", "image", "link", "display_order", "active"]


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ["question", "answer", "priority", "active"]


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["title", "description", "image", "active", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class DeliveryWeightSlabForm(forms.ModelForm):
    class Meta:
        model = DeliveryWeightSlab
        fields = ["min_weight", "max_weight", "charge", "is_active", "priority"]
        widgets = {
            "min_weight": forms.NumberInput(attrs={"step": "0.001", "min": "0"}),
            "max_weight": forms.NumberInput(attrs={"step": "0.001", "min": "0"}),
            "charge": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        self.instance.min_weight = cleaned.get("min_weight")
        self.instance.max_weight = cleaned.get("max_weight")
        self.instance.charge = cleaned.get("charge") or 0
        self.instance.is_active = cleaned.get("is_active", True)
        self.instance.priority = cleaned.get("priority") or 0
        self.instance.clean()
        return cleaned
