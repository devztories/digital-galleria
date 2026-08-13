# Digital Galleria

**Memories. Made Personal.**

A complete Django e-commerce platform for personalized frames, gifts, keepsakes
and craft items — built from scratch with manual UPI payments, per-product
delivery charges, original-quality customization uploads, gender-based
theming/tracking, a premium admin dashboard, and a draggable robot chatbot.

---

## 1. Requirements

- Python 3.10+
- Windows, macOS, or Linux

## 2. Windows Setup

```bat
cd Digital_Galleria_FINAL_COMPLETE

py -3.10 -m venv venv

venv\Scripts\activate

python -m pip install -r requirements.txt

python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser

python manage.py seed_demo

python manage.py check

python manage.py runserver
```

## 2b. macOS / Linux Setup

```bash
cd Digital_Galleria_FINAL_COMPLETE
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py check
python manage.py runserver
```

Then open **http://127.0.0.1:8000/**

---

## 3. First-Time Admin Configuration

Login to the Django admin at **/django-admin/** with your superuser account,
and the premium business dashboard at **/dashboard/** (staff-only).

Recommended setup order:

1. **Site Settings** (`/django-admin/sitecontent/sitesettings/`) — brand name,
   tagline, logo, hero content, about content, footer text.
2. **UPI / QR** — inside Site Settings: UPI ID, QR code image, payment
   instructions. These power the manual UPI payment screen.
3. **WhatsApp URL** — inside Site Settings, used by the "Send images via
   WhatsApp" customization option and the footer link. Never hard-coded.
4. **Your Story images** (`StorySlide`) — upload multiple images, each with
   its own title/subtitle/duration in seconds. The homepage story player
   reads durations from the database, not hard-coded values.
5. **Banners** (`Banner`) — homepage promotional banners with start/end
   dates; only currently-active banners are shown.
6. **Advertisements** (`Advertisement`) — choose a target section (homepage
   banner, product section, offer section, between products, promotional
   strip), optional gender targeting, and whether it's a full-screen popup
   (off by default).
7. **Categories** (`Category`) — Photo Frames, Personalized Frames,
   Polaroids, Gifts, Craft Items, Keepsakes, etc.
8. **Products** (`Product`) — set price, original price, discount, stock,
   whether it's customizable, max custom images, and **delivery charge**
   (every product has its own, admin-controlled, always used server-side).
9. **Offers** (`Offer`) — with optional gender targeting (Everyone / Male /
   Female). Visibility is driven only by the logged-in user's saved gender,
   never by their theme.
10. **Coupons** (`Coupon`) — percentage or fixed, with minimum order,
    maximum discount, usage limits and validity dates. All discount math is
    recalculated server-side at checkout; the frontend value is never trusted.
11. **Chatbot FAQs** (`FAQ`) — question, answer, keywords, priority. The
    chatbot matches these first, then falls back to product-aware and
    topic-based replies.
12. **Expenses** (via `/dashboard/expenses/`) — record business expenses to
    see live Profit/Loss on the dashboard.

## 4. Demo Data

`python manage.py seed_demo` creates sample categories, products, a
SiteSettings record (with generated placeholder images/QR — replace with
your real logo/QR/photos), story slides, banners, an advertisement, offers
(including gender-targeted ones), coupons (`WELCOME10`, `FLAT100`), and FAQs.
It is **safe to run more than once** — it will not duplicate existing
categories/products, and only creates the one-time content (story slides,
banners, etc.) if none exist yet.

The site also boots correctly with a **completely empty database** — none of
the seed data is required for the application to function.

## 5. Where Customization Images Live

Customer-uploaded customization images are stored **exactly as uploaded**
(no re-encoding, resizing, or compression) under:

```
media/customizations/originals/
```

Each file gets a random, non-guessable filename, so customers cannot access
another customer's images through predictable URLs.

**Admin downloads:**

- Order detail (`/dashboard/orders/<order_number>/`) shows every original
  image with its filename, dimensions, file size, and upload date, plus
  **View Full Size** and **Download** buttons that return the untouched
  original file.
- **Download All Original Images (ZIP)** bundles every original file for
  that order into a single ZIP (`ZIP_STORED`, i.e. no re-compression of the
  images themselves), safely renaming any duplicate filenames.

## 6. Manual UPI Payment Flow

Digital Galleria does **not** use Razorpay or any payment gateway. At
checkout, the customer is shown the UPI ID and QR code from Site Settings,
pays manually, and uploads a screenshot. Admin then verifies or rejects the
payment from the order detail page, which updates the order status.

```
Checkout → UPI QR → Customer Pays → Upload Screenshot → Payment Submitted
→ Admin Verification → Payment Verified → Processing → Shipped → Delivered
```

## 7. Gender vs. Theme

Gender and theme are two independent fields on the user model.

- Registration sets **gender** via two card-style choices (not a dropdown).
- On first save, a default **theme** is derived from gender (Male → Dark,
  Female → Light) — but this only happens once, at account creation.
- Changing theme afterwards in Settings never changes the stored gender.
- Gender-based logic — offer targeting, order-tracking vehicle animation
  (scooter for female, bike for male) — reads `user.gender` (or an order's
  frozen `gender_snapshot`) exclusively. Theme is never used for this.

## 8. Delivery Charge Rule

Every product has its own admin-controlled `delivery_charge`. The documented
business rule used throughout cart/checkout: **each line item's delivery
charge is `product.delivery_charge × quantity`, and the cart/order delivery
total is the sum of all line items' delivery charges.** This is always
calculated server-side from the stored product field — the frontend never
supplies or overrides a delivery value.

## 9. Project Structure

```
digital_galleria/
├── manage.py
├── requirements.txt
├── config/            # settings, root urls
├── accounts/          # custom User model, auth, settings, profile
├── categories/
├── products/
├── cart/
├── customization/     # original image upload/preservation
├── orders/             # checkout, snapshots, tracking
├── payments/           # manual UPI proof + verification
├── coupons/
├── offers/
├── advertisements/
├── chatbot/             # FAQ + product-aware bot
├── sitecontent/         # SiteSettings, Your Story, Banners, home/about
├── analytics/           # premium admin dashboard, expenses, order ops
├── templates/
└── static/
```

## 10. Notes

- `AUTH_USER_MODEL = 'accounts.User'` — all user relationships use
  `settings.AUTH_USER_MODEL`, never a direct FK to `auth.User`.
- All monetary fields use `Decimal`, never floats.
- `DEBUG = True` and a development `SECRET_KEY` are used for local/dev
  purposes only — change both before any real deployment.


## Chatbot outside-click behavior
When the floating chatbot is open, clicking anywhere outside the chatbot window or its toggle closes the floating window. Clicking inside the chatbot does not close it.


## Order line_total fix
Order line totals are now None-safe, so the admin order change page does not crash when an existing order item has a missing price or quantity. Missing values are treated as 0 for display/calculation.
