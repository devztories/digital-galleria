"""
Typo-tolerant product search.

Combines exact/substring matching (fast, exact relevance) with a fuzzy
fallback using Python's stdlib difflib (SequenceMatcher) so queries like
"iphon" or "iphnoe" still surface "iPhone 16". No extra dependencies.
"""
from difflib import SequenceMatcher
from products.models import Product

FUZZY_THRESHOLD = 0.62  # similarity ratio (0-1) below which we don't bother suggesting


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _best_token_similarity(query: str, text: str) -> float:
    """Highest similarity between the query and any whitespace-separated token in text,
    plus a nudge from the whole-string ratio — handles both single-word typos and
    matches buried inside a longer product name."""
    if not text:
        return 0.0
    whole = _similarity(query, text)
    tokens = text.split()
    token_best = max((_similarity(query, t) for t in tokens), default=0.0)
    return max(whole, token_best)


def search_products(query: str, queryset=None, limit: int = 8):
    """
    Returns a list of Product instances ranked by relevance:
    1. Exact name/brand/category startswith
    2. Substring contains
    3. Fuzzy (typo-tolerant) match on name/brand, above FUZZY_THRESHOLD

    Deduplicated, most relevant first.
    """
    query = (query or "").strip()
    if not query:
        return []

    base = queryset if queryset is not None else Product.objects.filter(active=True)
    seen_ids = set()
    ranked = []

    def add(qs_or_list, score_base):
        for p in qs_or_list:
            if p.id in seen_ids:
                continue
            seen_ids.add(p.id)
            ranked.append((score_base, p))

    starts = base.filter(name__istartswith=query)
    add(starts, 3.0)

    contains = base.filter(name__icontains=query)
    add(contains, 2.0)

    brand_or_cat = base.filter(brand__icontains=query) | base.filter(category__name__icontains=query)
    add(brand_or_cat.distinct(), 1.5)

    if len(ranked) < limit:
        # Fuzzy fallback: score every remaining active product by similarity.
        remaining = base.exclude(id__in=seen_ids)[:500]  # cap scan size for performance
        scored = []
        for p in remaining:
            sim = max(
                _best_token_similarity(query, p.name),
                _best_token_similarity(query, p.brand or ""),
            )
            if sim >= FUZZY_THRESHOLD:
                scored.append((sim, p))
        scored.sort(key=lambda t: t[0], reverse=True)
        for sim, p in scored:
            if p.id in seen_ids:
                continue
            seen_ids.add(p.id)
            ranked.append((sim, p))

    ranked.sort(key=lambda t: t[0], reverse=True)
    return [p for _, p in ranked[:limit]]
