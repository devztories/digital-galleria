"""One-click colour themes for Admin → Site Settings → Global Theme.

Every preset sets every colour token, so switching is a complete re-skin.
`dark` tokens drive the dark appearance, `light_*` tokens the light one.
"""

_COMMON_KEYS = [
    "background", "surface", "surface_alt", "text", "muted_text", "heading", "accent", "accent_secondary",
    "button", "button_text", "button_hover", "border", "input_background", "input_text", "card", "header", "footer",
    "search_background", "chatbot_background", "chatbot_surface", "chatbot_text", "chatbot_accent", "success", "danger",
    "admin_background", "admin_surface", "light_background", "light_surface", "light_text", "light_muted_text",
    "light_border", "light_accent", "light_accent_secondary", "light_button", "light_button_text", "light_button_hover",
    "default_animation_color_1", "default_animation_color_2", "default_animation_color_3",
]

PRESETS = {
    "burgundy": {
        "label": "Luxury Burgundy",
        "blurb": "Deep burgundy, warm ivory and champagne gold.",
        "swatches": ["#14080c", "#d9b878", "#f5ede0", "#7a1f33"],
        "tokens": {
            "background": "#14080c", "surface": "#1d0e14", "surface_alt": "#28141c", "text": "#f5ede0",
            "muted_text": "#b8a597", "heading": "#fff8ec", "accent": "#d9b878", "accent_secondary": "#a3324b",
            "button": "#d9b878", "button_text": "#2a0d15", "button_hover": "#f5ede0", "border": "#3d202b",
            "input_background": "#210f17", "input_text": "#f5ede0", "card": "#1f0f16", "header": "#14080c",
            "footer": "#0e0508", "search_background": "#210f17", "chatbot_background": "#1d0e14",
            "chatbot_surface": "#28141c", "chatbot_text": "#f5ede0", "chatbot_accent": "#d9b878",
            "success": "#8fc49f", "danger": "#e5727f", "admin_background": "#10060a", "admin_surface": "#1a0c12",
            "light_background": "#f8f1e5", "light_surface": "#fffaf1", "light_text": "#2b1017",
            "light_muted_text": "#7b6a68", "light_border": "#e6d8c1", "light_accent": "#7a1f33",
            "light_accent_secondary": "#b08d4f", "light_button": "#6e1a2c", "light_button_text": "#fbf4e6",
            "light_button_hover": "#8b2a40", "default_animation_color_1": "#d9b878",
            "default_animation_color_2": "#f6e8c9", "default_animation_color_3": "#b8924a",
        },
    },
    "ivory": {
        "label": "Warm Ivory & Gold",
        "blurb": "Bright ivory shop with burgundy text and gold detail.",
        "swatches": ["#f8f1e5", "#7a1f33", "#b08d4f", "#2b1017"],
        "tokens": {
            "background": "#f8f1e5", "surface": "#fffaf1", "surface_alt": "#f1e7d6", "text": "#2b1017",
            "muted_text": "#7b6a68", "heading": "#3a0f1b", "accent": "#7a1f33", "accent_secondary": "#b08d4f",
            "button": "#6e1a2c", "button_text": "#fbf4e6", "button_hover": "#8b2a40", "border": "#e6d8c1",
            "input_background": "#fffdf8", "input_text": "#2b1017", "card": "#fffaf1", "header": "#f8f1e5",
            "footer": "#efe3cf", "search_background": "#fffdf8", "chatbot_background": "#fffaf1",
            "chatbot_surface": "#f1e7d6", "chatbot_text": "#2b1017", "chatbot_accent": "#7a1f33",
            "success": "#2f7d55", "danger": "#b3263e", "admin_background": "#f4ecdd", "admin_surface": "#fffaf1",
            "light_background": "#f8f1e5", "light_surface": "#fffaf1", "light_text": "#2b1017",
            "light_muted_text": "#7b6a68", "light_border": "#e6d8c1", "light_accent": "#7a1f33",
            "light_accent_secondary": "#b08d4f", "light_button": "#6e1a2c", "light_button_text": "#fbf4e6",
            "light_button_hover": "#8b2a40", "default_animation_color_1": "#7a1f33",
            "default_animation_color_2": "#b08d4f", "default_animation_color_3": "#7a1f33",
        },
    },
    "neon": {
        "label": "Neon Cyber",
        "blurb": "Black with cyan, magenta and yellow.",
        "swatches": ["#05070a", "#00e5ff", "#ff2bd6", "#ffd60a"],
        "tokens": {
            "background": "#05070a", "surface": "#0b0e14", "surface_alt": "#11151d", "text": "#eef3f8",
            "muted_text": "#8a94a8", "heading": "#ffffff", "accent": "#00e5ff", "accent_secondary": "#ff2bd6",
            "button": "#00e5ff", "button_text": "#04070a", "button_hover": "#ffd60a", "border": "#1e2431",
            "input_background": "#0d1119", "input_text": "#eef3f8", "card": "#0d1117", "header": "#05070a",
            "footer": "#030507", "search_background": "#0d1119", "chatbot_background": "#0b0e14",
            "chatbot_surface": "#11151d", "chatbot_text": "#eef3f8", "chatbot_accent": "#ff2bd6",
            "success": "#35e0a1", "danger": "#ff4d6d", "admin_background": "#04060a", "admin_surface": "#0b0e14",
            "light_background": "#f2f8fb", "light_surface": "#ffffff", "light_text": "#0a0e14",
            "light_muted_text": "#5b6678", "light_border": "#d3dee7", "light_accent": "#0097ad",
            "light_accent_secondary": "#c9189f", "light_button": "#00b8d4", "light_button_text": "#03161a",
            "light_button_hover": "#e6b800", "default_animation_color_1": "#00e5ff",
            "default_animation_color_2": "#ff2bd6", "default_animation_color_3": "#ffd60a",
        },
    },
    "emerald": {
        "label": "Emerald Noir",
        "blurb": "Dark emerald, ivory and brushed gold.",
        "swatches": ["#07120e", "#c9a85c", "#eef0e6", "#1f6b4f"],
        "tokens": {
            "background": "#07120e", "surface": "#0d1c16", "surface_alt": "#132a21", "text": "#eef0e6",
            "muted_text": "#9fb0a4", "heading": "#fbfbf3", "accent": "#c9a85c", "accent_secondary": "#2f8f6b",
            "button": "#c9a85c", "button_text": "#0a1a13", "button_hover": "#eef0e6", "border": "#1f3a2e",
            "input_background": "#0f2019", "input_text": "#eef0e6", "card": "#0e1f18", "header": "#07120e",
            "footer": "#040b08", "search_background": "#0f2019", "chatbot_background": "#0d1c16",
            "chatbot_surface": "#132a21", "chatbot_text": "#eef0e6", "chatbot_accent": "#c9a85c",
            "success": "#7fd1a0", "danger": "#e5727f", "admin_background": "#050e0a", "admin_surface": "#0b1913",
            "light_background": "#f3f4ea", "light_surface": "#fcfdf6", "light_text": "#10261c",
            "light_muted_text": "#667569", "light_border": "#dcdfcd", "light_accent": "#1f6b4f",
            "light_accent_secondary": "#a8883f", "light_button": "#1d5f46", "light_button_text": "#f6f8ee",
            "light_button_hover": "#27795a", "default_animation_color_1": "#c9a85c",
            "default_animation_color_2": "#eef0e6", "default_animation_color_3": "#2f8f6b",
        },
    },
}

DEFAULT_PRESET = "burgundy"

for _key, _preset in PRESETS.items():
    missing = set(_COMMON_KEYS) - set(_preset["tokens"])
    assert not missing, f"preset {_key} missing {missing}"
