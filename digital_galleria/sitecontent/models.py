from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class SiteSettings(models.Model):
    """Singleton-style configuration. Only one active record is enforced in save()."""
    brand_name = models.CharField(max_length=100, default='Digital Galleria')
    tagline = models.CharField(max_length=200, default='Memories. Made Personal.')
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)

    whatsapp_url = models.CharField(max_length=255, blank=True, help_text='e.g. https://wa.me/91XXXXXXXXXX')
    instagram_url = models.CharField(max_length=255, blank=True)
    facebook_url = models.CharField(max_length=255, blank=True)

    upi_id = models.CharField(max_length=100, blank=True)
    qr_code = models.ImageField(upload_to='site/', blank=True, null=True)
    payment_instructions = models.TextField(blank=True, default='Scan the QR code or pay to the UPI ID above, then upload your payment screenshot.')

    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    footer_text = models.CharField(max_length=255, default='With love, Team Digital Galleria.')

    about_heading = models.CharField(max_length=200, blank=True, default='About Digital Galleria')
    about_description = models.TextField(blank=True)
    about_image = models.ImageField(upload_to='site/', blank=True, null=True)
    about_mission = models.TextField(blank=True)
    about_values = models.TextField(blank=True)

    hero_heading = models.CharField(max_length=200, blank=True, default='Moments. Made personal.')
    hero_subheading = models.TextField(blank=True, default='Premium frames, gifts and keepsakes crafted around your favourite people and memories.')
    hero_image = models.ImageField(upload_to='site/', blank=True, null=True)
    hero_button_text = models.CharField(max_length=50, blank=True, default='Explore Collection')
    hero_button_url = models.CharField(max_length=255, blank=True, default='/products/')

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            # Enforce singleton: update the existing record instead of creating a new one
            self.pk = SiteSettings.objects.first().pk
        super().save(*args, **kwargs)

    def __str__(self):
        return self.brand_name

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj


class StorySlide(models.Model):
    image = models.ImageField(upload_to='story/')
    title = models.CharField(max_length=150, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=4)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title or f'Story slide #{self.pk}'


class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    title = models.CharField(max_length=150, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    button_text = models.CharField(max_length=50, blank=True)
    button_url = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title or f'Banner #{self.pk}'

    def is_current(self):
        now = timezone.now()
        return self.active and self.start_date <= now <= self.end_date

    @classmethod
    def current(cls):
        now = timezone.now()
        return cls.objects.filter(active=True, start_date__lte=now, end_date__gte=now)
