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

SIMPLE NAMES (no admin picking needed) -- just name the file after the thing:

    <category name>_cover.jpg      e.g.  Wall Art_cover.jpg / wall-art_cover.png
    <product name>1.jpg, 2.jpg ... e.g.  Ceramic Vase1.jpg, Ceramic Vase2.jpg
    <product name>.jpg             single image

Matching ignores case, spaces, '_' and '-' (so "Ceramic Vase1", "ceramic-vase_1"
and "ceramic_vase1" are the same), and works with .jpg .jpeg .png .webp .avif .gif.
As soon as a category / product with that name exists (added in the admin), its
pictures show up automatically. 1 = main picture.
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




def _norm(text):
    """'Ceramic Vase_1' -> 'ceramic-vase-1' (case/space/underscore insensitive)."""
    text = re.sub(r"[\s_]+", "-", (text or "").lower())
    text = re.sub(r"[^a-z0-9-]", "", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def _candidates(*names):
    out = []
    for n in names:
        n = _norm(n)
        if n and n not in out:
            out.append(n)
    return out


def _simple_cover(cands):
    wanted = {f"{c}-cover" for c in cands}
    for name in list_names():
        if _norm(Path(name).stem) in wanted:
            return name
    return ""


def _simple_product(cands):
    """Files '<product>1', '<product>_2' ... (numbered, one per number) or '<product>'."""
    numbered, single = {}, []
    for name in list_names():
        stem = _norm(Path(name).stem)
        for c in cands:
            if stem == c:
                single.append(name)
                break
            m = re.fullmatch(re.escape(c) + r"-?(\d+)", stem)
            if m:
                numbered.setdefault(int(m.group(1)), name)  # 1.jpg and 1.webp -> keep one
                break
    if numbered:
        return [numbered[k] for k in sorted(numbered)]
    return single[:1]


def category_cover(category_slug, category_name=None):
    simple = _simple_cover(_candidates(category_slug, category_name))
    if simple:
        return library_url(simple)
    for name in list_names():
        if Path(name).stem.lower() in (f"{category_slug}__cover", f"{category_slug}___cover"):
            return library_url(name)
    return ""


def product_images(category_slug, product_slug, product_name=None):
    """Ordered image URLs for one product ('' category -> uncategorised)."""
    simple = _simple_product(_candidates(product_slug, product_name))
    if simple:
        return [library_url(n) for n in simple]
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
