"""Tests for the Oxblood redesign round: public order tracking, back-navigation
hooks, cleaned-up account/checkout pages, swipe-only gallery and the WhatsApp-only
confirmation checkbox."""
from decimal import Decimal

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from categories.models import Category
from orders.models import Order
from products.models import Product


PLAIN_STATIC = {"STORAGES": {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}}


def make_user(email="u@example.com"):
    return User.objects.create_user(email=email, name="Test User", password="1234", phone="9999999999")


@override_settings(**PLAIN_STATIC)
class PublicTrackingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user()
        self.order = Order.objects.create(
            user=self.user, customer_name_snapshot="Secret Name", phone_snapshot="9876543210",
            email_snapshot="u@example.com", delivery_address_snapshot="Private street 12",
            grand_total=Decimal("500"), order_status="shipped",
        )
        self.pending = Order.objects.create(
            user=self.user, customer_name_snapshot="X", phone_snapshot="1", email_snapshot="u@example.com",
            delivery_address_snapshot="Y", order_status="awaiting_payment",
        )

    def test_about_page_renders_with_track_box(self):
        resp = Client().get(reverse("about"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "TRACK ANY ORDER")

    def test_anyone_can_track_without_login_and_no_private_data_leaks(self):
        resp = Client().get(reverse("about"), {"order": self.order.order_number})
        self.assertContains(resp, self.order.order_number)
        self.assertContains(resp, "Shipped")
        for private in ("Secret Name", "9876543210", "Private street 12", "u@example.com"):
            self.assertNotContains(resp, private)

    def test_lowercase_and_number_only_ids_work(self):
        number = self.order.order_number
        for raw in (number.lower(), " # " + number, number[2:]):
            resp = Client().get(reverse("about"), {"order": raw})
            self.assertContains(resp, "data-track-result data-status", msg_prefix=raw)

    def test_unconfirmed_and_unknown_orders_are_not_found(self):
        for raw in (self.pending.order_number, "DG999999", "zzz"):
            resp = Client().get(reverse("about"), {"order": raw})
            self.assertContains(resp, "couldn")  # "couldn't find an order"
            self.assertNotContains(resp, "data-track-result data-status")

    def test_lookups_are_throttled(self):
        c = Client()
        for _ in range(30):
            c.get(reverse("about"), {"order": "DG1"})
        resp = c.get(reverse("about"), {"order": self.order.order_number})
        self.assertContains(resp, "Too many lookups")


@override_settings(**PLAIN_STATIC)
class AccountPagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def test_section_pages_have_no_settings_dropdown_and_go_back_home(self):
        for name in ("accounts:profile", "accounts:my_orders", "accounts:addresses",
                     "accounts:settings", "accounts:change_password", "accounts:hub",
                     "accounts:settings_vehicle", "accounts:settings_customization"):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, name)
            self.assertNotContains(resp, "account-nav-mobile", msg_prefix=name)
            self.assertNotContains(resp, "settings-select", msg_prefix=name)
            self.assertContains(resp, "window.DG_BACK_HOME=true", msg_prefix=name)

    def test_normal_pages_do_not_force_back_home(self):
        resp = self.client.get(reverse("products:list"))
        self.assertContains(resp, "window.DG_BACK_HOME=false")


@override_settings(**PLAIN_STATIC)
class StorefrontPagesTests(TestCase):
    def setUp(self):
        self.cat_a = Category.objects.create(name="Frames")
        self.cat_b = Category.objects.create(name="Mugs")
        self.p1 = Product.objects.create(name="Frame One", sku="F1", price=Decimal("100"), stock=5, category=self.cat_a)
        self.p2 = Product.objects.create(name="Mug One", sku="M1", price=Decimal("80"), stock=5, category=self.cat_b)

    def test_product_page_has_no_gallery_arrows_and_shows_other_products(self):
        resp = Client().get(reverse("products:detail", args=[self.p1.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "data-gallery-prev")
        self.assertNotContains(resp, "data-gallery-next")
        self.assertContains(resp, "You may also love")
        self.assertContains(resp, "Mug One")  # a product from ANOTHER category

    def test_home_and_about_render(self):
        self.assertEqual(Client().get("/").status_code, 200)
        self.assertEqual(Client().get(reverse("about")).status_code, 200)


@override_settings(**PLAIN_STATIC)
class CheckoutPagesTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Gifts")
        self.p = Product.objects.create(name="Gift", sku="G1", price=Decimal("100"), stock=5, category=cat,
                                        first_item_delivery_charge=Decimal("40"))
        self.client = Client()
        self.client.force_login(make_user("c@example.com"))
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 1})

    def test_stepper_boxes_are_gone_and_forms_are_not_cached(self):
        resp = self.client.get(reverse("orders:checkout_step1"))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "checkout-stepper")
        self.assertIn("no-store", resp.headers.get("Cache-Control", ""))


@override_settings(**PLAIN_STATIC)
class WhatsAppOnlyConfirmationTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Custom")
        self.p = Product.objects.create(
            name="Photo Mug", sku="PM1", price=Decimal("250"), stock=10, category=cat,
            customizable=True, customization_image_mode=Product.CUSTOMIZATION_MODE_WHATSAPP,
        )
        self.client = Client()
        self.client.force_login(make_user("w@example.com"))
        self.url = reverse("customization:customize", args=[self.p.slug])

    def test_page_shows_checkbox_and_buttons_start_disabled(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, 'name="wa_images_sent"')
        self.assertContains(resp, "I have sent my images through WhatsApp")
        html = resp.content.decode()
        self.assertRegex(html, r'id="direct-checkout-btn"[^>]*disabled')

    def test_direct_checkout_blocked_without_confirmation(self):
        resp = self.client.post(self.url, {"action": "direct_checkout", "via_whatsapp": "on", "quantity": 1})
        self.assertEqual(resp.status_code, 200)  # re-rendered with an error, no redirect
        self.assertNotIn("buy_now", self.client.session)

    def test_direct_checkout_allowed_after_confirmation(self):
        resp = self.client.post(self.url, {"action": "direct_checkout", "via_whatsapp": "on",
                                           "wa_images_sent": "on", "quantity": 1})
        self.assertRedirects(resp, reverse("orders:checkout"), fetch_redirect_response=False)
        self.assertIn("buy_now", self.client.session)

    def test_both_mode_products_do_not_need_the_checkbox(self):
        self.p.customization_image_mode = Product.CUSTOMIZATION_MODE_BOTH
        self.p.save()
        resp = self.client.post(self.url, {"action": "direct_checkout", "via_whatsapp": "on", "quantity": 1})
        self.assertRedirects(resp, reverse("orders:checkout"), fetch_redirect_response=False)
