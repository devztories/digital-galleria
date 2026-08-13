from django.db import models
from django.utils import timezone

TARGET_SECTION_CHOICES = (
    ('homepage_banner', 'Homepage Banner'),
    ('product_section', 'Product Section'),
    ('offer_section', 'Offer Section'),
    ('between_products', 'Between Product Cards'),
    ('promotional_strip', 'Promotional Strip'),
)

GENDER_CHOICES = (
    ('all', 'Everyone'),
    ('male', 'Male'),
    ('female', 'Female'),
)


class Advertisement(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to='ads/')
    description = models.TextField(blank=True)
    cta_text = models.CharField(max_length=50, default='Learn More')
    cta_url = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    target_section = models.CharField(max_length=32, choices=TARGET_SECTION_CHOICES, default='homepage_banner')
    target_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='all')
    full_screen_popup = models.BooleanField(default=False, help_text='Only enable for special campaigns')

    class Meta:
        ordering = ['priority']

    def __str__(self):
        return self.title

    @classmethod
    def visible_for(cls, section, user):
        now = timezone.now()
        qs = cls.objects.filter(active=True, target_section=section, start_date__lte=now, end_date__gte=now)
        gender = getattr(user, 'gender', '') if getattr(user, 'is_authenticated', False) else ''
        if gender in ('male', 'female'):
            qs = qs.filter(models.Q(target_gender='all') | models.Q(target_gender=gender))
        else:
            qs = qs.filter(target_gender='all')
        return qs
