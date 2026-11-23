"""Hard-coded (in-repo) image catalogue.

Instead of uploading images through the admin (and depending on Supabase /
ephemeral disks), image files can be committed to the project under

    static/catalog/<category-slug>/_cover.webp                 -> category cover
    static/catalog/<category-slug>/<product-slug>/1.webp ...   -> product images (1 = main)
    static/catalog/<category-slug>/<product-slug>/<colour-slug>/1.webp ... -> images of ONE colour
    static/catalog/<category-slug>/<product-slug>.webp         -> single-image shortcut

What exists (categories / products / colours) is listed in products/catalog_data.py.

Names are matched purely by slug, so adding a category + products in the admin
and dropping files into the matching folders is all it takes — no model fields,
no upload. An image uploaded in the admin always wins over the static one, so
nothing existing breaks.
"""
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.templatetags.static import static
from django.utils.text import slugify

CATALOG_ROOT = Path(settings.BASE_DIR) / "static" / "catalog"
IMAGE_EXTS = {".webp", ".jpg", ".jpeg", ".png", ".avif", ".gif"}
COVER_STEMS = ("_cover", "cover")


def _natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _scan():
    index = {}
    if not CATALOG_ROOT.is_dir():
        return index
    for path in CATALOG_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            rel = path.relative_to(CATALOG_ROOT)
            index.setdefault(rel.parent.as_posix(), []).append(rel.name)
    for files in index.values():
        files.sort(key=_natural)
    return index


@lru_cache(maxsize=1)
def _cached_index():
    return _scan()


def index():
    # While developing, re-scan on every request so new files show up instantly.
    return _scan() if settings.DEBUG else _cached_index()


def _url(rel_path):
    path = f"catalog/{rel_path}"
    try:
        return static(path)
    except ValueError:  # manifest storage + collectstatic not re-run yet
        return f"{settings.STATIC_URL}{path}"


def category_cover(category_slug):
    files = index().get(category_slug, [])
    for stem in COVER_STEMS:
        for f in files:
            if Path(f).stem.lower() == stem:
                return _url(f"{category_slug}/{f}")
    return ""


def product_images(category_slug, product_slug):
    """Ordered list of image URLs for one product ('' category -> uncategorised folder)."""
    base = category_slug or "_uncategorised"
    idx = index()
    folder = idx.get(f"{base}/{product_slug}")
    if folder:
        return [_url(f"{base}/{product_slug}/{f}") for f in folder]
    return [_url(f"{base}/{f}") for f in idx.get(base, []) if Path(f).stem.lower() == product_slug.lower()]


def colour_slug(colour_name):
    """Folder name used for a colour: 'Natural Oak' -> 'natural-oak'."""
    return slugify(colour_name or "")


def variant_images(category_slug, product_slug, colour_name):
    """Ordered image URLs for ONE colour of a product:
    static/catalog/<category>/<product>/<colour-slug>/1.webp, 2.webp ..."""
    base = category_slug or "_uncategorised"
    folder = f"{base}/{product_slug}/{colour_slug(colour_name)}"
    return [_url(f"{folder}/{f}") for f in index().get(folder, [])]


def expected_paths(category_slug, product_slug=None, colour_name=None):
    base = category_slug or "_uncategorised"
    if product_slug is None:
        return f"static/catalog/{base}/_cover.webp"
    if colour_name:
        return f"static/catalog/{base}/{product_slug}/{colour_slug(colour_name)}/1.webp"
    return f"static/catalog/{base}/{product_slug}/1.webp"
