# Digital Galleria — Premium Admin-Controlled E-commerce

This build preserves the existing Django architecture while adding the premium UI/design-control layer and the requested delivery/customization/payment/tracking enhancements.

## Run locally

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

Primary custom control panel:

`/admin/`

Framework Django admin remains available only as a fallback at `/django-admin/`.

## New control areas

- Site & Design Settings — `/admin/site-settings/`
- Global theme tokens and page-level overrides
- Branding, UPI, QR, success sound and business settings
- Configurable illustrations/assets with SVG safety checks
- Animation controls and reduced-motion support
- Weight-based or product-count delivery mode
- Weight slabs and count-based delivery rules
- Product multiple-image gallery upload/reorder/primary-image controls
- Multiple customization image uploads and optional WhatsApp flow
- Separate checkout steps and admin-controlled UPI payment page
- Customer order tracking and cancellation/refund state

## Delivery configuration

Checkout is intentionally blocked with a clear administrator warning if the selected delivery mode has no active rules. This prevents accidental zero-charge delivery caused by missing configuration.

## Existing functionality

Existing accounts, products, categories, cart, orders, coupons, payment-proof flow, custom admin, storage manager, and reports are retained. The custom admin remains the primary administration interface.


## Luxury redesign, notifications & hard-coded images

- **Theme (fixed)**: Deep Aubergine `#26143B` + Soft Lilac `#A88BC5` + Warm Gold `#D6AE55` + Lavender White `#F6F0FA`. The colours are defined once in `site_settings/palette.py` and styled by `static/css/theme-luxe.css`. They are **not editable from the admin panel** (Global Theme / Page Themes screens and the customer light/dark toggle were removed). To change the look, edit `palette.py` / `theme-luxe.css` and redeploy. The old `ThemeSettings` / `PageTheme` tables are kept only so existing migrations stay valid; their values are ignored.
- **Admin notifications**: bell in the admin top bar + live pop-ups + `/admin/notifications/`. Triggered by: new order (payment proof submitted), payment re-submitted, order cancelled, new customization, new customer, low/out of stock.
- **Admin push notifications** (works with the tab closed): run `python manage.py generate_vapid_keys`, set `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_ADMIN_EMAIL`, then click **Enable push** in the bell panel on each device. Needs HTTPS (your production domain is fine; `localhost` also works).
- **Customization mode per product** (Admin -> Products -> Add/Edit, when *Customizable* is ticked): *WhatsApp / Direct*, *WhatsApp only*, *Direct only*.
- **Hard-coded catalogue (categories, products, colours + colour-wise images)**: data in `products/catalog_data.py`, pictures in `static/catalog/<category>/<product>/<colour>/1.webp…`, loaded by `python manage.py sync_catalog` (run from `build.sh`). See `static/catalog/README.md` and Admin -> Image Catalog. Admin can still add/override everything.

Run `python manage.py migrate` after deploying.


## Motion layer (animations)

- `static/css/motion.css` + `static/js/motion.js`, loaded from `templates/base.html`.
- Home page shuffles **every** admin-supplied image set (hero slides, stories, categories, featured/personal products, ads) on each page load (`home_views.py`).
- Scroll reveals (staggered), scroll-progress bar, hero Ken Burns + parallax + caption entrance, image fade-in on load, hover zoom + pointer glint on cards, endless marquee for ad images.
- Only `opacity` / `transform` / `translate` / `scale` are animated, one rAF scroll loop, IntersectionObserver for reveals - so it stays smooth on phones.
- Admin -> Site Settings -> Animations still controls it: **Enabled = off** disables everything, **Duration** and **Intensity** scale the reveals. Visitors with "reduce motion" enabled get a static page.
