from django.urls import resolve
from .models import SiteSettings, ThemeSettings, PageTheme, AssetSetting, AnimationSettings


def _theme_dict(theme):
    return {name: getattr(theme, name, "") for name in [
        "background", "surface", "surface_alt", "text", "muted_text", "heading", "accent", "button", "button_text",
        "button_hover", "border", "input_background", "input_text", "card", "header", "footer", "search_background", "chatbot_background", "chatbot_surface", "chatbot_text", "chatbot_accent",
        "success", "danger", "admin_background", "admin_surface", "light_background", "light_surface", "light_text",
        "light_muted_text", "light_border", "default_animation_color_1", "default_animation_color_2", "default_animation_color_3",
    ]}


def site_settings_context(request):
    site = SiteSettings.load()
    theme = ThemeSettings.load()
    animation = AnimationSettings.load()
    try:
        resolver = resolve(request.path)
        namespace = resolver.namespace or ""
        name = resolver.url_name or ""
        page_key = "home" if name == "home" else name
        scoped_map = {
            ("products", "list"): "products_list", ("products", "detail"): "product_detail",
            ("categories", "list"): "category", ("categories", "detail"): "category",
            ("cart", "cart"): "cart", ("orders", "checkout"): "checkout", ("payments", "pay"): "payment",
            ("payments", "success"): "payment_success", ("orders", "tracking"): "tracking",
            ("accounts", "profile"): "profile", ("accounts", "settings"): "profile",
            ("accounts", "register"): "register", ("accounts", "login"): "login",
            ("customization", "customize"): "customization", ("accounts", "my_orders"): "orders",
        }
        page_key = scoped_map.get((namespace, name), page_key)
        if name == "list" and request.GET.get("q"):
            page_key = "search"
    except Exception:
        page_key = ""
    page_theme = PageTheme.objects.filter(page_key=page_key).first() if page_key else None
    values = _theme_dict(theme)
    if page_theme:
        for key in list(values):
            value = getattr(page_theme, key, "")
            if value:
                values[key] = value
    assets = {a.key: a for a in AssetSetting.objects.filter(enabled=True)}
    return {
        "site_settings": site,
        "theme_settings": theme,
        "animation_settings": animation,
        "page_theme": page_theme,
        "theme_assets": assets,
        "theme_tokens": values,
    }
