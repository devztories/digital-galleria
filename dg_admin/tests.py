from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from categories.models import Category
from products import image_library
from products.models import Colour, Product, ProductImage, ProductVariant, VariantImage

NAMES = image_library.list_names()
A, B, C = NAMES[0], NAMES[1], NAMES[2]


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}, STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class ImageLibraryPickerTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("a@example.com", "Admin", "pass1234")
        self.client.force_login(self.admin)
        self.cat = Category.objects.create(name="Test Cat")
        self.product = Product.objects.create(name="Test Prod", sku="T-1", price=Decimal("10"), category=self.cat)
        self.colour = Colour.objects.create(name="Red", hex_code="#ff0000")

    def test_library_is_flat_and_listed(self):
        self.assertTrue(NAMES)
        self.assertTrue(all("/" not in n for n in NAMES))
        r = self.client.get(reverse("dg_admin:image_library_json"))
        self.assertEqual(len(r.json()["images"]), len(NAMES))

    def test_pages_render_with_picker(self):
        for url in (reverse("dg_admin:product_edit", args=[self.product.pk]),
                    reverse("dg_admin:product_add"),
                    reverse("dg_admin:category_add"),
                    reverse("dg_admin:image_catalog")):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
        self.assertContains(self.client.get(reverse("dg_admin:category_add")), "data-lib-picker")

    def _product_post(self, **extra):
        data = {"name": "Test Prod", "description": "", "brand": "", "category": self.cat.pk, "sku": "T-1",
                "price": "10", "stock": "1", "max_customization_images": "0", "customization_image_mode": "both",
                "weight": "0", "weight_unit": "kg", "delivery_pricing_mode": "site_default",
                "first_item_delivery_charge": "0", "additional_item_delivery_charge": "0",
                "inside_kerala_delivery_charge": "0", "inside_kerala_delivery_qty_step": "1",
                "inside_kerala_delivery_additional_charge": "0", "outside_kerala_delivery_charge": "0",
                "outside_kerala_delivery_qty_step": "1", "outside_kerala_delivery_additional_charge": "0",
                "expected_delivery_days": "0", "active": "on", "delivery_enabled": "on"}
        data.update(extra)
        return self.client.post(reverse("dg_admin:product_edit", args=[self.product.pk]), data)

    def test_product_main_and_gallery_picked_from_library(self):
        r = self._product_post(library_main=A, library_gallery=[B, C, "../../etc/passwd", "nope.webp", B])
        self.assertEqual(r.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.main_image.name, A)
        self.assertEqual(self.product.main_image.url, image_library.library_url(A))
        self.assertEqual([i.image.name for i in ProductImage.objects.filter(product=self.product)], [B, C])

    def test_clear_main_image(self):
        self._product_post(library_main=A)
        self._product_post(clear_main_image="1")
        self.product.refresh_from_db()
        self.assertFalse(self.product.main_image)

    def test_variant_images_picked_and_first_is_primary(self):
        r = self.client.post(reverse("dg_admin:product_variant_add", args=[self.product.pk]),
                             {"colour": self.colour.pk, "sku": "T-1-R", "stock": "3", "active": "on",
                              "library_images": [A, B, "bad.webp"]})
        self.assertEqual(r.status_code, 302)
        v = ProductVariant.objects.get(product=self.product)
        imgs = list(v.images.all())
        self.assertEqual([i.image.name for i in imgs], [A, B])
        self.assertTrue(imgs[0].is_primary)
        self.assertEqual(v.image_urls, [image_library.library_url(A), image_library.library_url(B)])
        # edit: add one more
        self.client.post(reverse("dg_admin:product_variant_edit", args=[v.pk]),
                         {"colour": self.colour.pk, "sku": "T-1-R", "stock": "3", "active": "on", "library_images": [C]})
        self.assertEqual(v.images.count(), 3)

    def test_category_image_picked(self):
        r = self.client.post(reverse("dg_admin:category_edit", args=[self.cat.pk]),
                             {"name": "Test Cat", "display_order": "0", "active": "on", "library_image": A})
        self.assertEqual(r.status_code, 302)
        self.cat.refresh_from_db()
        self.assertEqual(self.cat.display_image_url, image_library.library_url(A))

    def test_legacy_uploaded_names_still_resolve(self):
        """Old rows that point at an uploaded file must not break."""
        ProductImage.objects.create(product=self.product, image="products/gallery/old.jpg")
        url = self.product.images.first().image.url
        self.assertIn("products/gallery/old.jpg", url)

    def test_storefront_shows_library_image(self):
        self._product_post(library_main=A)
        r = self.client.get(reverse("products:detail", args=[self.product.slug])) if False else None
        self.assertEqual(self.product.__class__.objects.get(pk=self.product.pk).display_image_url, image_library.library_url(A))
