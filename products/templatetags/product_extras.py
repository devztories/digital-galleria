from django import template

register = template.Library()


@register.filter
def chunks(items, size=10):
    """Split a list/queryset into consecutive groups of `size` (default 10).

    Used by partials/product_rows.html so EVERY product listing on the site
    (home, categories, all products, "keep exploring") renders the same way:
    one swipeable row per 10 products, rows stacked top to bottom.
    """
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 10
    items = list(items or [])
    return [items[i:i + size] for i in range(0, len(items), size)]
