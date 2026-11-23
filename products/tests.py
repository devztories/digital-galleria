from django.test import TestCase

# Create your tests here.


class SimpleNameImageMatchingTests(TestCase):
    """Files named '<category>_cover.jpg' / '<product>1.jpg' are picked up automatically."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        from products import image_library, static_catalog
        self.tmp = tempfile.TemporaryDirectory()
        for n in ["Wall Art_cover.jpg", "Ceramic Vase1.jpg", "ceramic-vase_2.png", "Lonely Lamp.webp"]:
            (Path(self.tmp.name) / n).write_bytes(b"x")
        patcher = mock.patch.object(image_library, "LIBRARY_ROOT", Path(self.tmp.name))
        patcher.start()
        image_library._cached.cache_clear()  # library listing is cached outside DEBUG
        self.addCleanup(image_library._cached.cache_clear)
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.sc = static_catalog

    def test_category_cover(self):
        self.assertIn("Wall%20Art_cover.jpg", self.sc.category_cover("wall-art", "Wall Art"))
        self.assertEqual(self.sc.category_cover("gifts", "Gifts"), "")

    def test_product_numbered_images_in_order(self):
        urls = self.sc.product_images("home-decor", "ceramic-vase", "Ceramic Vase")
        self.assertEqual(len(urls), 2)
        self.assertIn("Ceramic%20Vase1.jpg", urls[0])
        self.assertIn("ceramic-vase_2.png", urls[1])

    def test_single_image_and_missing(self):
        self.assertEqual(len(self.sc.product_images("x", "lonely-lamp", "Lonely Lamp")), 1)
        self.assertEqual(self.sc.product_images("x", "nothing", "Nothing"), [])
