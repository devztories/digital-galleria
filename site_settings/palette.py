"""FIXED storefront + admin palette  —  OXBLOOD · BURGUNDY · DUSTY ROSE · CHAMPAGNE

    #4A0D14  oxblood      - header, footer, admin sidebar, headings
    #800020  burgundy     - buttons, links, strong accents
    #CFA0A2  dusty rose   - secondary accent, soft borders, decorative detail
    #F7E7CE  champagne    - page tint, highlights on dark surfaces

These colours are deliberately NOT editable from the admin panel. Every colour
the templates use comes from this dictionary (see context_processors.py), so
changing the look means editing this one file (and static/css/theme-luxe.css +
static/css/oxblood.css), never a settings form.
"""

# --- the four brand colours -------------------------------------------------
OXBLOOD = "#4A0D14"
BURGUNDY = "#800020"
DUSTY_ROSE = "#CFA0A2"
CHAMPAGNE = "#F7E7CE"

# --- shades derived from them ----------------------------------------------
OX_900 = "#2E070C"         # footer, deepest shade
OX_800 = OXBLOOD           # header, admin sidebar, headings
BURG_700 = BURGUNDY        # buttons
BURG_600 = "#9B1B3A"       # button hover
SURFACE = "#FFFBF6"        # cards / inputs (champagne-white)
SURFACE_DEEP = "#F4E0C8"   # alt surface (champagne, a touch deeper)
ACCENT_TEXT = "#8A3B43"    # rose-burgundy used as TEXT on champagne (readable contrast)
PAGE_BG = "#FBF3E8"        # page background (champagne, lightened)
INK = "#2B0D12"            # body text
MUTED = "#755a5e"          # secondary text
BORDER = "#EBD3C6"         # hairlines (dusty-rose / champagne tint)

THEME = {
    "background": PAGE_BG, "surface": SURFACE, "surface_alt": SURFACE_DEEP,
    "text": INK, "muted_text": MUTED, "heading": OX_800,
    "accent": ACCENT_TEXT, "accent_secondary": DUSTY_ROSE,
    "button": BURG_700, "button_text": "#fff8ef", "button_hover": BURG_600,
    "border": BORDER, "input_background": "#fffdf9", "input_text": INK,
    "card": SURFACE, "header": OX_800, "footer": OX_900,
    "search_background": "#fffdf9",
    "success": "#2f7d55", "danger": "#a61e2e",
    "admin_background": "#f6e8d6", "admin_surface": SURFACE,
    # The site is single-theme (champagne), so the "light" tokens simply mirror it.
    "light_background": PAGE_BG, "light_surface": SURFACE, "light_text": INK,
    "light_muted_text": MUTED, "light_border": BORDER,
    "light_accent": ACCENT_TEXT, "light_accent_secondary": DUSTY_ROSE,
    "light_button": BURG_700, "light_button_text": "#fff8ef", "light_button_hover": BURG_600,
    # Brand-name shimmer (sits on the oxblood header): champagne -> gold -> rose tint
    "default_animation_color_1": "#fbefd9", "default_animation_color_2": CHAMPAGNE, "default_animation_color_3": "#efd2cf",
    "heading_font": "serif",
}
