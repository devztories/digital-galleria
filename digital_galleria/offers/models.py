from django.db import models
from django.utils import timezone

TARGET_CHOICES = (
    ('all', 'Everyone'),
    ('male', 'Male'),
    ('female', 'Female'),
)


class Offer(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='offers/', blank=True, null=True)
    discount_text = models.CharField(max_length=50, help_text='e.g. "10% OFF"')
    cta_text = models.CharField(max_length=50, default='Shop Now')
    cta_url = models.CharField(max_length=255, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    target_gender = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

    def is_current(self):
        now = timezone.now()
        return self.active and self.start_date <= now <= self.end_date

    @classmethod
    def visible_for(cls, user):
        now = timezone.now()
        qs = cls.objects.filter(active=True, start_date__lte=now, end_date__gte=now)
        gender = getattr(user, 'gender', '') if getattr(user, 'is_authenticated', False) else ''
        if gender in ('male', 'female'):
            qs = qs.filter(models.Q(target_gender='all') | models.Q(target_gender=gender))
        else:
            qs = qs.filter(target_gender='all')
        return qs
