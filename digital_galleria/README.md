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

Existing accounts, products, categories, cart, orders, coupons, payment-proof flow, custom admin, storage manager, reports and chatbot functionality are retained. The custom admin remains the primary administration interface.
