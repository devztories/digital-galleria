# Hard-coded catalogue — where everything goes

Three things work together:

| What | Where | Purpose |
|---|---|---|
| **Data** (categories, products, colours, prices) | `products/catalog_data.py` | the one list of what the shop sells |
| **Pictures** | `static/catalog/...` (this folder) | named by slug, picked up automatically |
| **Loader** | `python manage.py sync_catalog` | copies the data file into the database (runs in `build.sh` on every deploy) |

## Folder layout (names are slugs: lower-case, hyphens)

```
static/catalog/
  <category>/_cover.webp                      category cover          1200x800
  <category>/<product>/<colour>/1.webp        colour image 1 (= main) 900x900
  <category>/<product>/<colour>/2.webp        colour image 2
  <category>/<product>/<colour>/3.webp        colour image 3
  <category>/<product>/1.webp, 2.webp ...     product WITHOUT colours (or fallback)
```

Example:
`static/catalog/photo-frames/wooden-photo-frame/natural-oak/1.webp`

* Aim for **3 images per colour** (front / angle / detail) — `IMAGES_PER_COLOUR` in `catalog_data.py`.
* Any of `.webp .jpg .png .avif .gif` works; files show in natural order (`2` before `10`).
* If a colour has no pictures the product's own pictures (or the first colour that has some) are shown instead.

## Add a new product (3 steps)

1. Add a dict to `PRODUCTS` in `products/catalog_data.py` (name, slug, sku, price, `colours=[...]`).
   New colour? add `"Name": "#hex"` to `COLOURS` first. New category? add it to `CATEGORIES`.
2. Drop the pictures at `static/catalog/<category>/<product>/<colour>/1.webp ...`
3. `python manage.py sync_catalog` (or redeploy). Check progress with `python manage.py sync_catalog --check`
   or in **Admin → Image Catalog**.

## Replace the placeholder pictures

The pictures that ship with the project are generated placeholders (they say "placeholder").
Overwrite them with real photos using the **same file names** — nothing else changes.
`python scripts/generate_placeholder_images.py` redraws placeholders only for files that are missing
(add `--force` to redraw everything, which would overwrite real photos — be careful).

## Admin can still add things

* Products / categories / colours / images added in **Admin** work exactly as before and sit next to the hard-coded ones.
* An image uploaded in the admin **always wins** over the hard-coded file for that product / colour / category.
* `sync_catalog` only creates what is missing; it never edits or deletes, so prices and stock changed in the admin are safe.
* Not hard-coded (stay in the database): customer customization uploads and the colour "preview shapes" editor.
