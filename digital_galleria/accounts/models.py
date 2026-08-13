from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    THEME_CHOICES = (
        ('dark', 'Dark'),
        ('light', 'Light'),
    )

    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Set default theme based on gender ONLY at creation time and only
        # if the theme hasn't been explicitly customised yet.
        if not self.pk and not getattr(self, '_theme_explicitly_set', False):
            if self.gender == 'female':
                self.theme = 'light'
            elif self.gender == 'male':
                self.theme = 'dark'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        return self.name or self.username
