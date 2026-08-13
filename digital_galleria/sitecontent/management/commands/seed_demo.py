import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from PIL import Image, ImageDraw, ImageFont

from categories.models import Category
from products.models import Product
from offers.models import Offer
from coupons.models import Coupon
from chatbot.models import FAQ
from sitecontent.models import SiteSettings, StorySlide, Banner
from advertisements.models import Advertisement


PALETTE = ['#8b5cf6', '#6d28d9', '#a78bfa', '#e7c98f', '#2c2636', '#1a1622']


def make_image(text, size=(900, 900), bg=None):
    bg = bg or random.choice(PALETTE)
    img = Image.new('RGB', size, bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    bbox = draw.textbbox((0, 0), text, font=font) if font else (0, 0, len(text) * 6, 11)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), text, fill='#f8f7fb', font=font)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f'{text.lower().replace(" ", "_")}.jpg')


class Command(BaseCommand):
    help = 'Seed Digital Galleria with demo data. Safe to run more than once.'

    def handle(self, *args, **options):
        now = timezone.now()

        # --- Site Settings ---
        settings_obj = SiteSettings.load()
        if not settings_obj.upi_id:
            settings_obj.upi_id = 'digitalgalleria@upi'
            settings_obj.whatsapp_url = 'https://wa.me/919999999999'
            settings_obj.instagram_url = 'https://instagram.com/digitalgalleria'
            settings_obj.facebook_url = 'https://facebook.com/digitalgalleria'
            settings_obj.contact_email = 'hello@digitalgalleria.example'
            settings_obj.contact_phone = '+91 99999 99999'
            settings_obj.about_description = (
                'Digital Galleria crafts personalized frames, keepsakes and gifts '
                'around the people and moments you love most.'
            )
            settings_obj.about_mission = 'To turn everyday memories into treasured, tangible keepsakes.'
            settings_obj.about_values = 'Craftsmanship, personalization, and care in every detail.'
            if not settings_obj.qr_code:
                settings_obj.qr_code.save('demo_qr.jpg', make_image('UPI QR'), save=False)
            if not settings_obj.hero_image:
                settings_obj.hero_image.save('hero.jpg', make_image('Digital Galleria', size=(900, 1100)), save=False)
            if not settings_obj.about_image:
                settings_obj.about_image.save('about.jpg', make_image('Our Story'), save=False)
            settings_obj.save()
            self.stdout.write(self.style.SUCCESS('Site settings created.'))

        # --- Categories ---
        cat_data = [
            ('Photo Frames', 'Frames for your favourite prints.'),
            ('Personalized Frames', 'Frames engraved and customized just for you.'),
            ('Polaroids', 'Instant-style personalized polaroid prints.'),
            ('Gifts', 'Thoughtful personalized gifting.'),
            ('Craft Items', 'Handcrafted keepsakes and decor.'),
            ('Keepsakes', 'Small treasures made to last.'),
        ]
        categories = {}
        for i, (name, desc) in enumerate(cat_data):
            cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc, 'display_order': i})
            if created and not cat.image:
                cat.image.save(f'{name}.jpg', make_image(name), save=True)
            categories[name] = cat
        self.stdout.write(self.style.SUCCESS(f'{len(categories)} categories ready.'))

        # --- Products ---
        product_data = [
            ('Classic Wooden Photo Frame', 'Photo Frames', 499, 60, True, 3, True),
            ('Engraved Name Frame', 'Personalized Frames', 899, 0, True, 4, True),
            ('Retro Polaroid Set (x6)', 'Polaroids', 349, 40, True, 6, True),
            ('Memory Jar Gift Box', 'Gifts', 699, 50, False, 1, True),
            ('Handmade Photo Album', 'Craft Items', 1199, 0, True, 20, True),
            ('Mini Keepsake Locket', 'Keepsakes', 599, 30, True, 1, True),
            ('Family Collage Frame', 'Personalized Frames', 999, 60, True, 5, True),
            ('Birthday Surprise Box', 'Gifts', 799, 40, False, 1, False),
        ]
        for name, cat_name, price, delivery, customizable, max_imgs, featured in product_data:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults=dict(
                    category=categories[cat_name],
                    short_description=f'A beautiful {name.lower()} from Digital Galleria.',
                    description=f'{name} — crafted with care, personalized around your memories.',
                    keywords=f'{name}, {cat_name}, gift, personalized, frame',
                    price=price,
                    original_price=price + 200,
                    discount_percent=10,
                    stock=random.randint(0, 30),
                    active=True,
                    featured=featured,
                    customizable=customizable,
                    max_custom_images=max_imgs,
                    delivery_charge=delivery,
                ),
            )
            if created and not product.main_image:
                product.main_image.save(f'{name}.jpg', make_image(name), save=True)
        self.stdout.write(self.style.SUCCESS('Demo products ready.'))

        # --- Story slides ---
        if not StorySlide.objects.exists():
            for i, (title, duration) in enumerate([
                ('Every Frame Tells a Story', 3), ('Crafted Around You', 5), ('Made to Keep Forever', 4)
            ]):
                slide = StorySlide.objects.create(title=title, subtitle='Digital Galleria', display_order=i, duration_seconds=duration)
                slide.image.save(f'story_{i}.jpg', make_image(title, size=(720, 1040)), save=True)
            self.stdout.write(self.style.SUCCESS('Story slides created.'))

        # --- Banners ---
        if not Banner.objects.exists():
            banner = Banner.objects.create(
                title='Festive Personalization Sale', subtitle='Up to 20% off custom frames',
                button_text='Shop Now', button_url='/products/', display_order=0,
                start_date=now - timedelta(days=1), end_date=now + timedelta(days=60),
            )
            banner.image.save('banner1.jpg', make_image('Festive Sale', size=(1200, 700)), save=True)
            banner2 = Banner.objects.create(
                title='New: Handcrafted Albums', subtitle='Preserve every chapter',
                button_text='Explore', button_url='/products/', display_order=1,
                start_date=now - timedelta(days=1), end_date=now + timedelta(days=60),
            )
            banner2.image.save('banner2.jpg', make_image('New Albums', size=(1200, 700)), save=True)
            self.stdout.write(self.style.SUCCESS('Banners created.'))

        # --- Advertisements ---
        if not Advertisement.objects.exists():
            ad = Advertisement.objects.create(
                title='Free Delivery Weekend', description='Free delivery on all orders above ₹999 this weekend.',
                cta_text='Shop Now', cta_url='/products/', priority=0, target_section='promotional_strip',
                start_date=now - timedelta(days=1), end_date=now + timedelta(days=30),
            )
            ad.image.save('ad1.jpg', make_image('Free Delivery'), save=True)
            self.stdout.write(self.style.SUCCESS('Advertisements created.'))

        # --- Offers ---
        if not Offer.objects.exists():
            Offer.objects.create(
                title='Weekend Special', description='Extra savings on all personalized frames.',
                discount_text='10% OFF', cta_text='Shop Now', cta_url='/products/',
                start_date=now - timedelta(days=1), end_date=now + timedelta(days=30), target_gender='all', display_order=0,
            )
            Offer.objects.create(
                title="Men's Exclusive", description='A special discount for our male customers.',
                discount_text='10% OFF', cta_text='Shop Now', cta_url='/products/',
                start_date=now - timedelta(days=1), end_date=now + timedelta(days=30), target_gender='male', display_order=1,
            )
            Offer.objects.create(
                title="Women's Special", description='A special discount for our female customers.',
                discount_text='15% OFF', cta_text='Shop Now', cta_url='/products/',
                start_date=now - timedelta(days=1), end_date=now + timedelta(days=30), target_gender='female', display_order=2,
            )
            self.stdout.write(self.style.SUCCESS('Offers created.'))

        # --- Coupons ---
        if not Coupon.objects.exists():
            Coupon.objects.create(
                code='WELCOME10', discount_type='percentage', discount_value=10, minimum_order=500,
                start_date=now - timedelta(days=1), expiry_date=now + timedelta(days=90), usage_limit=0,
            )
            Coupon.objects.create(
                code='FLAT100', discount_type='fixed', discount_value=100, minimum_order=999,
                start_date=now - timedelta(days=1), expiry_date=now + timedelta(days=90), usage_limit=100,
            )
            self.stdout.write(self.style.SUCCESS('Coupons created.'))

        # --- FAQs ---
        if not FAQ.objects.exists():
            faqs = [
                ('How can I customize a product?', 'Open a customizable product and tap "Customize This Piece" to upload photos or add a message.', 'customize, personalize', 10),
                ('How do I pay?', 'We use manual UPI payment. Scan the QR code or use our UPI ID at checkout, then upload your screenshot.', 'pay, payment, upi', 9),
                ('Where can I see my order?', 'Go to Settings → Orders to view and track all your orders.', 'order, track, status', 8),
                ('Can I send images through WhatsApp?', 'Yes — on the customization page, tick "Send images via WhatsApp" instead of uploading directly.', 'whatsapp, images', 7),
                ('What offers are available?', 'Check the Offers section on our homepage for current deals, some tailored just for you.', 'offer, discount, deal', 6),
            ]
            for q, a, kw, pr in faqs:
                FAQ.objects.create(question=q, answer=a, keywords=kw, priority=pr)
            self.stdout.write(self.style.SUCCESS('FAQs created.'))

        self.stdout.write(self.style.SUCCESS('Demo data seeding complete.'))
