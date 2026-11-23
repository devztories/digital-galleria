from .models import SiteSettings, AssetSetting, AnimationSettings
from .palette import THEME


def site_settings_context(request):
    """Template context. Colours are FIXED (site_settings/palette.py) — the
    ThemeSettings / PageTheme tables are intentionally ignored so the admin
    panel can't change the look of the site."""
    site = SiteSettings.load()
    animation = AnimationSettings.load()
    assets = {a.key: a for a in AssetSetting.objects.filter(enabled=True)}
    return {
        "site_settings": site,
        "animation_settings": animation,
        "theme_assets": assets,
        "theme_tokens": dict(THEME),
    }
