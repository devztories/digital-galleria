from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User, Address
from categories.models import Category
from products.models import Product
from coupons.models import Coupon
from django.utils import timezone
from datetime import timedelta

from orders.services.delivery import calculate_line_delivery, calculate_total_delivery
from orders.models import Order


class PasswordLengthTests(TestCase):
    def test_valid_passwords(self):
        for pwd in ["1234", "abcd", "test", "123456", "abc123", "A@1b"]:
            self.assertTrue(4 <= len(pwd) <= 8)

    def test_invalid_passwords(self):
        for pwd in ["123", "123456789"]:
            self.assertFalse(4 <= len(pwd) <= 8)

    def test_registration_rejects_short_password(self):
        client = Client()
        resp = client.post(reverse("accounts:register"), {
            "name": "A", "email": "a@example.com", "phone": "1",
            "password": "12", "confirm_password": "12",
        })
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertFalse(User.objects.filter(email="a@example.com").exists())

    def test_registration_accepts_valid_password(self):
        client = Client()
        resp = client.post(reverse("accounts:register"), {
            "name": "A", "email": "b@example.com", "phone": "1",
            "password": "1234", "confirm_password": "1234",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(email="b@example.com").exists())


class DeliveryCalculationTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Test Cat")
        self.product_a = Product.objects.create(
            name="Product A", sku="A", price=Decimal("100"), stock=100, category=cat,
            first_item_delivery_charge=Decimal("50"), additional_item_delivery_charge=Decimal("20"),
        )
        self.product_b = Product.objects.create(
            name="Product B", sku="B", price=Decimal("100"), stock=100, category=cat,
            first_item_delivery_charge=Decimal("80"), additional_item_delivery_charge=Decimal("30"),
        )
        self.product_free = Product.objects.create(
            name="Product Free", sku="F", price=Decimal("100"), stock=100, category=cat, free_delivery=True,
        )

    def test_single_product_formula(self):
        self.assertEqual(calculate_line_delivery(self.product_a, 1), Decimal("50"))
        self.assertEqual(calculate_line_delivery(self.product_a, 2), Decimal("70"))
        self.assertEqual(calculate_line_delivery(self.product_a, 3), Decimal("90"))
        self.assertEqual(calculate_line_delivery(self.product_a, 4), Decimal("110"))

    def test_product_b_formula(self):
        self.assertEqual(calculate_line_delivery(self.product_b, 1), Decimal("80"))
        self.assertEqual(calculate_line_delivery(self.product_b, 2), Decimal("110"))
        self.assertEqual(calculate_line_delivery(self.product_b, 3), Decimal("140"))

    def test_free_delivery_is_zero(self):
        self.assertEqual(calculate_line_delivery(self.product_free, 5), Decimal("0.00"))

    def test_combined_cart_delivery(self):
        lines = [(self.product_a, 2), (self.product_b, 3)]
        self.assertEqual(calculate_total_delivery(lines), Decimal("210"))  # 70 + 140


class DirectCheckoutTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat")
        self.a = Product.objects.create(name="A", sku="PA", price=Decimal("10"), stock=10, category=cat)
        self.b = Product.objects.create(name="B", sku="PB", price=Decimal("20"), stock=10, category=cat)
        self.c = Product.objects.create(name="C", sku="PC", price=Decimal("30"), stock=10, category=cat)
        self.user = User.objects.create_user(email="u@example.com", name="U", password="1234")
        self.client = Client()
        self.client.force_login(self.user)
        Address.objects.create(
            user=self.user, full_name="U", phone="1", house_building="H", street="S",
            city="City", state="State", pincode="000000", is_default=True,
        )

    def test_direct_checkout_contains_only_selected_product(self):
        # Put A and C in cart
        self.client.post(reverse("cart:add", args=[self.a.id]), {"quantity": 1})
        self.client.post(reverse("cart:add", args=[self.c.id]), {"quantity": 1})
        # Buy Now on B
        self.client.post(reverse("cart:buy_now", args=[self.b.id]), {"quantity": 1})
        resp = self.client.get(reverse("orders:checkout"))
        content = resp.content.decode()
        self.assertIn("B", content)
        # Place the order
        address = Address.objects.get(user=self.user)
        self.client.post(reverse("orders:place_order"), {"address_id": address.id})

        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product_name_snapshot, "B")

    def test_cart_preserved_after_direct_checkout(self):
        self.client.post(reverse("cart:add", args=[self.a.id]), {"quantity": 1})
        self.client.post(reverse("cart:add", args=[self.c.id]), {"quantity": 1})
        self.client.post(reverse("cart:buy_now", args=[self.b.id]), {"quantity": 1})
        address = Address.objects.get(user=self.user)
        self.client.post(reverse("orders:place_order"), {"address_id": address.id})

        cart_resp = self.client.get(reverse("cart:cart"))
        content = cart_resp.content.decode()
        self.assertIn("A", content)
        self.assertIn("C", content)
        self.assertNotIn(">B<", content)


class OrderNumberLookupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="t@example.com", name="T", password="1234")

    def test_order_lookup_uses_order_number_not_pk(self):
        order = Order.objects.create(
            user=self.user, customer_name_snapshot="T", phone_snapshot="1",
            email_snapshot="t@example.com", delivery_address_snapshot="addr",
        )
        resp = self.client.get(reverse("orders:tracking", args=[order.order_number]))
        self.assertEqual(resp.status_code, 200)


class CancelledOrderTests(TestCase):
    def test_cancelled_order_has_no_status_progress(self):
        user = User.objects.create_user(email="c@example.com", name="C", password="1234")
        order = Order.objects.create(
            user=user, customer_name_snapshot="C", phone_snapshot="1",
            email_snapshot="c@example.com", delivery_address_snapshot="addr", order_status="cancelled",
        )
        self.assertEqual(order.status_progress(), [])


class ExpectedDeliveryTests(TestCase):
    def test_admin_can_update_expected_delivery(self):
        staff = User.objects.create_superuser(email="admin2@example.com", name="Admin2", password="1234")
        user = User.objects.create_user(email="d@example.com", name="D", password="1234")
        order = Order.objects.create(
            user=user, customer_name_snapshot="D", phone_snapshot="1",
            email_snapshot="d@example.com", delivery_address_snapshot="addr",
        )
        client = Client()
        client.force_login(staff)
        client.post(reverse("dg_admin:order_detail", args=[order.order_number]), {
            "order_status": "processing", "expected_delivery_date": "2026-09-01", "notes": "",
        })
        order.refresh_from_db()
        self.assertEqual(str(order.expected_delivery_date), "2026-09-01")


class FuzzySearchTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Test Cat")
        Product.objects.create(name="Wooden Photo Frame", sku="WPF", price=Decimal("10"), stock=5, category=cat, active=True)
        Product.objects.create(name="Custom Photo Mug", sku="CPM", price=Decimal("10"), stock=5, category=cat, active=True)

    def test_typo_tolerant_match(self):
        from products.services.search import search_products
        results = search_products("wodden fram")
        self.assertTrue(any(p.name == "Wooden Photo Frame" for p in results))

    def test_irrelevant_query_returns_nothing(self):
        from products.services.search import search_products
        results = search_products("completely unrelated nonsense zzz")
        self.assertEqual(results, [])

    def test_search_suggestions_endpoint(self):
        resp = self.client.get(reverse("products:search_suggestions"), {"q": "wodden"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(any(r["name"] == "Wooden Photo Frame" for r in data["results"]))


class TrackingVehicleTests(TestCase):
    def test_default_vehicle_is_bike(self):
        user = User.objects.create_user(email="v@example.com", name="V", password="1234")
        self.assertEqual(user.preferred_vehicle, "bike")

    def test_user_can_switch_to_scooter(self):
        user = User.objects.create_user(email="v2@example.com", name="V2", password="1234")
        client = Client()
        client.force_login(user)
        client.post(reverse("accounts:settings"), {"vehicle": "scooter"})
        user.refresh_from_db()
        self.assertEqual(user.preferred_vehicle, "scooter")

    def test_tracking_page_uses_preferred_vehicle(self):
        user = User.objects.create_user(email="v3@example.com", name="V3", password="1234", preferred_vehicle="scooter")
        order = Order.objects.create(
            user=user, customer_name_snapshot="V3", phone_snapshot="1",
            email_snapshot="v3@example.com", delivery_address_snapshot="addr", order_status="shipped",
        )
        resp = self.client.get(reverse("orders:tracking", args=[order.order_number]))
        self.assertContains(resp, "vehicle-scooter.svg")


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(email="super@example.com", name="Super", password="1234")
        self.staff = User.objects.create_user(email="staff@example.com", name="Staff", password="1234", is_staff=True)
        self.client = Client()

    def test_non_superuser_cannot_create_admin_user(self):
        self.client.force_login(self.staff)
        resp = self.client.post(reverse("dg_admin:admin_user_add"), {
            "name": "New Admin", "email": "new@example.com", "phone": "1",
            "password": "1234", "is_active": "on",
        })
        # staff_required for other admin pages passes, but dg_superuser_required should redirect (302 to login)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_superuser_can_create_admin_user(self):
        self.client.force_login(self.superuser)
        resp = self.client.post(reverse("dg_admin:admin_user_add"), {
            "name": "New Admin", "email": "new@example.com", "phone": "1",
            "password": "1234", "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        new_user = User.objects.get(email="new@example.com")
        self.assertTrue(new_user.is_staff)
        self.assertTrue(new_user.check_password("1234"))

    def test_new_admin_requires_password(self):
        self.client.force_login(self.superuser)
        resp = self.client.post(reverse("dg_admin:admin_user_add"), {
            "name": "No Pass", "email": "nopass@example.com", "phone": "1", "is_active": "on",
        })
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertFalse(User.objects.filter(email="nopass@example.com").exists())

    def test_superuser_cannot_remove_own_access(self):
        self.client.force_login(self.superuser)
        self.client.post(reverse("dg_admin:admin_user_remove_access", args=[self.superuser.id]))
        self.superuser.refresh_from_db()
        self.assertTrue(self.superuser.is_staff)

    def test_superuser_can_deactivate_other_admin(self):
        self.client.force_login(self.superuser)
        self.client.post(reverse("dg_admin:admin_user_toggle_active", args=[self.staff.id]))
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_active)

    def test_removing_access_keeps_account_and_history(self):
        self.client.force_login(self.superuser)
        self.client.post(reverse("dg_admin:admin_user_remove_access", args=[self.staff.id]))
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_staff)
        self.assertTrue(User.objects.filter(email="staff@example.com").exists())
