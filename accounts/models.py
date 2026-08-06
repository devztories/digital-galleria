from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.CharField(
        max_length=15,
        blank=True,
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.username


class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ("home", "Home"),
        ("office", "Office"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default="home",
    )

    full_name = models.CharField(max_length=150)

    phone = models.CharField(max_length=15)

    address_line1 = models.CharField(max_length=255)

    address_line2 = models.CharField(
        max_length=255,
        blank=True,
    )

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    pincode = models.CharField(max_length=10)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at"]

    def save(self, *args, **kwargs):
        if not self.pk:
            if not Address.objects.filter(user=self.user).exists():
                self.is_default = True

        super().save(*args, **kwargs)

        if self.is_default:
            Address.objects.filter(user=self.user).exclude(
                pk=self.pk
            ).update(is_default=False)

    @property
    def full_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.pincode,
        ]
        return ", ".join([p for p in parts if p])

    def __str__(self):
        return f"{self.full_name} ({self.get_address_type_display()})"