"""HARD-CODED CATALOGUE  —  the single place that lists every category,
product and colour of the shop.

HOW IT WORKS
------------
1. This file says *what exists*   (categories, products, colours, prices).
2. static/catalog/ holds *the pictures* (named by slug, see below).
3. `python manage.py sync_catalog` copies this file into the database
   (it runs automatically from build.sh on every deploy).

Nothing here is locked: the admin panel keeps working exactly as before.
  * sync_catalog only ever CREATES missing rows — it never overwrites a price,
    stock figure or description that an admin has edited.
  * An image uploaded in the admin always wins over a hard-coded one.
  * Products / categories / colours added in the admin simply sit next to the
    hard-coded ones.

WHERE THE IMAGES GO   (slug = lower-case name with hyphens)
-------------------------------------------------------
    static/catalog/<category>/_cover.webp                       category cover
    static/catalog/<category>/<product>/<colour>/1.webp         colour image 1 (= main)
    static/catalog/<category>/<product>/<colour>/2.webp         colour image 2 ...
    static/catalog/<category>/<product>/1.webp                  product WITHOUT colours
                                                                (or fallback for any colour)

HOW TO ADD SOMETHING NEW
------------------------
  New category : add a row to CATEGORIES            + drop  <category>/_cover.webp
  New product  : add a dict to PRODUCTS             + drop  <category>/<product>/<colour>/1.webp ...
  New colour   : add it to the product's "colours"  (and to COLOURS if it is a brand-new colour)
  Then run `python manage.py sync_catalog` (or just redeploy).
  `python manage.py sync_catalog --check` lists every image that is still missing.
"""

# How many pictures each colour (or each colour-less product) should have.
# Used only for the "missing images" report — more or fewer files still work.
IMAGES_PER_COLOUR = 3
IMAGE_SIZE_HINT = "900 x 900 px, square, .webp (or .jpg/.png), under 200 KB each"
CATEGORY_COVER_HINT = "1200 x 800 px, landscape, .webp"

# ---------------------------------------------------------------------------
# COLOURS  — name -> hex.  Product variants refer to these by name.
# ---------------------------------------------------------------------------
COLOURS = {
    "Walnut": "#5C4033",
    "Natural Oak": "#C8A165",
    "White": "#F5F5F0",
    "Black": "#1C1C1C",
    "Gold": "#D6AE55",
    "Rose": "#D98BA3",
    "Silver": "#B8BCC2",
    "Red": "#C0392B",
    "Ocean Blue": "#1F6F9F",
    "Sunset Orange": "#E8743B",
    "Emerald": "#1E8C62",
    "Terracotta": "#B5573A",
    "Ivory": "#F1E8D4",
    "Sage": "#9CAF88",
}

# ---------------------------------------------------------------------------
# CATEGORIES  — (name, display_order).  slug = slugify(name).
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("Photo Frames", 1),
    ("Wall Art", 2),
    ("Home Decor", 3),
    ("Gifts", 4),
    ("Accessories", 5),
]

# ---------------------------------------------------------------------------
# PRODUCTS
#   slug       : folder name under static/catalog/<category>/  (keep it stable!)
#   sku        : unique code. Colour variants get  <sku>-<COLOUR-SLUG>.
#   price      : MRP.   discount_price: selling price (None = no discount)
#   colours    : list of colour names from COLOURS.  [] = product has no colour options
#   stock      : stock PER COLOUR (or for the whole product if it has no colours)
#   kind       : drawing style used only by scripts/generate_placeholder_images.py
# ---------------------------------------------------------------------------
PRODUCTS = [
    # ---- Photo Frames -----------------------------------------------------
    dict(name="Wooden Photo Frame", slug="wooden-photo-frame", category="Photo Frames", sku="PF-001",
         price=799, discount_price=649, stock=25, featured=True, customizable=True, kind="frame",
         colours=["Walnut", "Natural Oak", "White"],
         description="Handcrafted wooden photo frame with a smooth matte finish."),
    dict(name="Personalized Name Frame", slug="personalized-name-frame", category="Photo Frames", sku="PF-002",
         price=1199, discount_price=None, stock=15, featured=True, bestseller=True, customizable=True, kind="frame",
         colours=["Black", "Gold", "Rose"],
         description="A frame personalised with your name and your favourite photo."),
    # ---- Wall Art ---------------------------------------------------------
    dict(name="Canvas Wall Art - Abstract", slug="canvas-wall-art-abstract", category="Wall Art", sku="WA-001",
         price=1499, discount_price=1299, stock=10, featured=True, kind="canvas",
         colours=["Ocean Blue", "Sunset Orange", "Emerald"],
         description="Gallery-wrapped abstract canvas that lifts any plain wall."),
    dict(name="Gallery Wall Collage Set", slug="gallery-wall-collage-set", category="Wall Art", sku="WA-002",
         price=2499, discount_price=2099, stock=8, featured=True, customizable=True, kind="collage",
         colours=["Black", "White"],
         description="Set of six frames in mixed sizes to build your own gallery wall."),
    # ---- Home Decor -------------------------------------------------------
    dict(name="LED Wall Clock", slug="led-wall-clock", category="Home Decor", sku="HD-001",
         price=999, discount_price=None, stock=30, kind="clock",
         colours=["Black", "White"],
         description="Silent sweep wall clock with a soft warm LED glow."),
    dict(name="Ceramic Vase", slug="ceramic-vase", category="Home Decor", sku="HD-002",
         price=899, discount_price=749, stock=20, featured=True, kind="vase",
         colours=["Terracotta", "Ivory", "Sage"],
         description="Hand-finished ceramic vase for fresh or dried flowers."),
    # ---- Gifts ------------------------------------------------------------
    dict(name="Custom Photo Mug", slug="custom-photo-mug", category="Gifts", sku="GF-001",
         price=449, discount_price=399, stock=50, featured=True, bestseller=True, customizable=True, kind="mug",
         colours=["White", "Black", "Red"],
         description="Dishwasher-safe ceramic mug printed with your own photo."),
    dict(name="Custom Puzzle Photo", slug="custom-puzzle-photo", category="Gifts", sku="GF-002",
         price=649, discount_price=None, stock=40, featured=True, customizable=True, kind="puzzle",
         colours=[],   # no colour options -> images go straight in the product folder
         description="Turn any photo into a 120-piece jigsaw puzzle."),
    # ---- Accessories ------------------------------------------------------
    dict(name="Engraved Keychain", slug="engraved-keychain", category="Accessories", sku="AC-001",
         price=299, discount_price=None, stock=100, bestseller=True, customizable=True, kind="keychain",
         colours=["Silver", "Gold", "Black"],
         description="Metal keychain engraved with a name, date or short message."),
]
