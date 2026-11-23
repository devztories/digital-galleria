"""Load the hard-coded catalogue (products/catalog_data.py) into the database.

    python manage.py sync_catalog            # create whatever is missing
    python manage.py sync_catalog --check    # only report missing images, change nothing

Safe to run on every deploy: it only CREATES missing categories / colours /
products / colour variants. It never edits or deletes anything, so prices,
stock and descriptions changed by an admin are left alone.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from categories.models import Category
from products import static_catalog as sc
from products.catalog_data import CATEGORIES, COLOURS, IMAGES_PER_COLOUR, PRODUCTS
from products.models import Colour, Product, ProductVariant


class Command(BaseCommand):
    help = "Create the hard-coded categories, colours, products and colour variants (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--check", action="store_true",
                            help="Only report which hard-coded images are missing; do not touch the database.")

    def handle(self, *args, **options):
        if not options["check"]:
            with transaction.atomic():
                self._sync()
        self._report_images()

    # ------------------------------------------------------------------
    def _sync(self):
        created = {"categories": 0, "colours": 0, "products": 0, "variants": 0}

        categories = {}
        for name, order in CATEGORIES:
            cat = Category.objects.filter(name__iexact=name).first()
            if cat is None:
                cat = Category.objects.create(name=name, display_order=order)
                created["categories"] += 1
            categories[name] = cat

        colours = {}
        for i, (name, hex_code) in enumerate(COLOURS.items()):
            colour = Colour.objects.filter(name__iexact=name).first()
            if colour is None:
                colour = Colour.objects.create(name=name, hex_code=hex_code, display_order=i)
                created["colours"] += 1
            colours[name] = colour

        for spec in PRODUCTS:
            product = (Product.objects.filter(sku=spec["sku"]).first()
                       or Product.objects.filter(slug=spec["slug"]).first())
            if product is None:
                product = Product.objects.create(
                    name=spec["name"], slug=spec["slug"], sku=spec["sku"],
                    category=categories[spec["category"]],
                    description=spec.get("description", ""),
                    price=Decimal(spec["price"]),
                    discount_price=Decimal(spec["discount_price"]) if spec.get("discount_price") else None,
                    stock=0 if spec["colours"] else spec.get("stock", 0),
                    featured=spec.get("featured", False),
                    bestseller=spec.get("bestseller", False),
                    customizable=spec.get("customizable", False),
                    active=True,
                )
                created["products"] += 1

            for order, colour_name in enumerate(spec["colours"]):
                colour = colours[colour_name]
                if ProductVariant.objects.filter(product=product, colour=colour).exists():
                    continue
                sku = f"{spec['sku']}-{slugify(colour_name).upper()}"
                if ProductVariant.objects.filter(sku=sku).exists():
                    continue
                ProductVariant.objects.create(
                    product=product, colour=colour, sku=sku,
                    stock=spec.get("stock", 0), display_order=order, active=True,
                )
                created["variants"] += 1

        self.stdout.write(self.style.SUCCESS(
            "Catalogue synced — created {categories} categories, {colours} colours, "
            "{products} products, {variants} colour variants.".format(**created)
        ))

    # ------------------------------------------------------------------
    def _report_images(self):
        """Compare catalog_data.py with what is actually inside static/image_library/."""
        missing = []
        for name, _order in CATEGORIES:
            slug = slugify(name)
            if not sc.category_cover(slug):
                missing.append(sc.expected_paths(slug))
        for spec in PRODUCTS:
            cat_slug = slugify(spec["category"])
            if spec["colours"]:
                for colour_name in spec["colours"]:
                    have = len(sc.variant_images(cat_slug, spec["slug"], colour_name))
                    if have < IMAGES_PER_COLOUR:
                        missing.append(f"{sc.expected_paths(cat_slug, spec['slug'], colour_name)}"
                                       f"   ({have}/{IMAGES_PER_COLOUR} images)")
            else:
                have = len(sc.product_images(cat_slug, spec["slug"]))
                if have < IMAGES_PER_COLOUR:
                    missing.append(f"{sc.expected_paths(cat_slug, spec['slug'])}   ({have}/{IMAGES_PER_COLOUR} images)")
        if missing:
            self.stdout.write(self.style.WARNING(f"{len(missing)} hard-coded image slot(s) incomplete:"))
            for line in missing:
                self.stdout.write(f"  - {line}")
        else:
            self.stdout.write(self.style.SUCCESS("All hard-coded images are in place."))
