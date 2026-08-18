from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from categories.models import Category
from products.models import Product
from site_settings.models import SiteSettings, HeroSlide, Story, FAQ
from coupons.models import Coupon


class Command(BaseCommand):
    help = "Seed demo data for Digital Galleria. Safe to run repeatedly."

    def handle(self, *args, **options):
        settings_obj = SiteSettings.load()
        if not settings_obj.store_name:
            settings_obj.store_name = "Digital Galleria"
        settings_obj.payment_instructions = settings_obj.payment_instructions or (
            "Scan the QR code or pay to the UPI ID above, then upload your payment screenshot."
        )
        settings_obj.contact_email = settings_obj.contact_email or "support@digitalgalleria.example"
        settings_obj.save()
        self.stdout.write(self.style.SUCCESS("Site settings ready."))

        categories_data = ["Photo Frames", "Wall Art", "Home Decor", "Gifts", "Accessories"]
        categories = {}
        for i, name in enumerate(categories_data):
            cat, _ = Category.objects.get_or_create(name=name, defaults={"display_order": i})
            categories[name] = cat
        self.stdout.write(self.style.SUCCESS(f"{len(categories)} categories ready."))

        products_data = [
            ("Wooden Photo Frame", "Photo Frames", 799, 649, 25, True, False, True, "PF-001"),
            ("Personalized Name Frame", "Photo Frames", 1199, None, 15, True, True, True, "PF-002"),
            ("Canvas Wall Art - Abstract", "Wall Art", 1499, 1299, 10, True, False, False, "WA-001"),
            ("LED Wall Clock", "Home Decor", 999, None, 30, False, False, False, "HD-001"),
            ("Custom Photo Mug", "Gifts", 449, 399, 50, True, True, True, "GF-001"),
            ("Engraved Keychain", "Accessories", 299, None, 100, False, True, True, "AC-001"),
            ("Ceramic Vase", "Home Decor", 899, 749, 20, True, False, False, "HD-002"),
            ("Custom Puzzle Photo", "Gifts", 649, None, 40, True, True, True, "GF-002"),
        ]
        for name, cat_name, price, discount, stock, featured, customizable, free_delivery, sku in products_data:
            Product.objects.get_or_create(
                sku=sku,
                defaults=dict(
                    name=name, category=categories[cat_name], price=Decimal(price),
                    discount_price=Decimal(discount) if discount else None, stock=stock,
                    featured=featured, customizable=customizable, active=True,
                    description=f"A premium {name.lower()} crafted for everyday elegance.",
                    delivery_enabled=True, free_delivery=free_delivery,
                    first_item_delivery_charge=Decimal("0.00") if free_delivery else Decimal("50.00"),
                    additional_item_delivery_charge=Decimal("0.00") if free_delivery else Decimal("20.00"),
                ),
            )
        self.stdout.write(self.style.SUCCESS(f"{len(products_data)} products ready."))

        FAQ.objects.get_or_create(
            question="How is delivery calculated?",
            defaults={"answer": "Delivery is calculated per product based on quantity and shown as a single combined charge at checkout.", "priority": 1},
        )
        FAQ.objects.get_or_create(
            question="How do I track my order?",
            defaults={"answer": "Visit 'My Orders' from your account, or use the tracking link sent after payment.", "priority": 2},
        )

        Coupon.objects.get_or_create(
            code="WELCOME10",
            defaults=dict(
                discount_type="percentage", discount_value=Decimal("10.00"), minimum_order=Decimal("500.00"),
                maximum_discount=Decimal("200.00"), start_date=timezone.now() - timedelta(days=1),
                expiry_date=timezone.now() + timedelta(days=90), usage_limit=0, per_user_limit=1, active=True,
            ),
        )
        self.stdout.write(self.style.SUCCESS("Sample coupon WELCOME10 ready."))
        self.stdout.write(self.style.SUCCESS("Seed data complete. (Hero/Story images need to be uploaded via /admin/ since they require real image files.)"))
