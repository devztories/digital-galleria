"""Auto-matching for the demo catalogue (products/catalog_data.py).

All images live in ONE flat folder, static/image_library/  (see image_library.py).
Files that follow the naming convention below are picked up automatically for
products that have no image chosen in the admin yet — this is what makes the
`sync_catalog` demo shop show pictures without any admin work:

    <category>__cover.webp                         category cover
    <category>__<product>__<colour>__1.webp, 2 ... one colour's pictures (1 = main)
    <category>__<product>__1.webp, 2 ...           product WITHOUT colours
    <category>__<product>.webp                     single-image shortcut

(<category> / <product> / <colour> are slugs: lower-case, hyphens.)
Anything the admin picks from the library always wins over this auto-matching.
"""
import re
from pathlib import Path

from django.utils.text import slugify

from .image_library import list_names, library_url


def _natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _names_with_prefix(prefix, exact_depth):
    """Library files whose stem is `prefix` + '__' + <exact_depth tokens>."""
    out = []
    for name in list_names():
        stem = Path(name).stem
        if not stem.startswith(prefix + "__"):
            continue
        rest = stem[len(prefix) + 2:].split("__")
        if len(rest) == exact_depth and (exact_depth == 0 or all(rest)):
            out.append(name)
    return sorted(out, key=_natural)


def category_cover(category_slug):
    for name in list_names():
        if Path(name).stem.lower() in (f"{category_slug}__cover", f"{category_slug}___cover"):
            return library_url(name)
    return ""


def product_images(category_slug, product_slug):
    """Ordered image URLs for one product ('' category -> uncategorised)."""
    base = category_slug or "_uncategorised"
    prefix = f"{base}__{product_slug}"
    names = [n for n in _names_with_prefix(prefix, 1) if Path(n).stem.rsplit("__", 1)[-1].isdigit()]
    single = [n for n in list_names() if Path(n).stem.lower() == prefix.lower()]
    return [library_url(n) for n in (names or single)]


def colour_slug(colour_name):
    """Token used for a colour: 'Natural Oak' -> 'natural-oak'."""
    return slugify(colour_name or "")


def variant_images(category_slug, product_slug, colour_name):
    """Ordered image URLs for ONE colour of a product."""
    base = category_slug or "_uncategorised"
    prefix = f"{base}__{product_slug}__{colour_slug(colour_name)}"
    names = _names_with_prefix(prefix, 1)
    single = [n for n in list_names() if Path(n).stem.lower() == prefix.lower()]
    return [library_url(n) for n in (names or single)]


def expected_paths(category_slug, product_slug=None, colour_name=None):
    base = category_slug or "_uncategorised"
    if product_slug is None:
        return f"static/image_library/{base}__cover.webp"
    if colour_name:
        return f"static/image_library/{base}__{product_slug}__{colour_slug(colour_name)}__1.webp"
    return f"static/image_library/{base}__{product_slug}__1.webp"
