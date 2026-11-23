from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

# Used to render the address "State" field as a dropdown instead of free
# text, so a delivery address can never be mis-typed into the wrong
# Kerala/Outside-Kerala bucket (e.g. "Ka", "Karnataka" typed for what should
# be "Kerala"). Kerala is listed first since it's this store's home state.
INDIAN_STATE_CHOICES = [(s, s) for s in [
    "Kerala",
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]]


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    theme_preference = models.CharField(
        max_length=10, choices=[("system", "System"), ("dark", "Dark"), ("light", "Light")], default="system"
    )
    preferred_vehicle = models.CharField(
        max_length=10, choices=[("bike", "Bike"), ("scooter", "Scooter")], default="bike",
        help_text="Which vehicle icon to show on this account's order tracking pages.",
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    house_building = models.CharField(max_length=200)
    street = models.CharField(max_length=200)
    area = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city}"

    @staticmethod
    def _norm(value):
        return (value or "").strip().casefold()

    @classmethod
    def find_duplicate(cls, user, data):
        """Finds an existing address for this user that's really the same
        physical address as `data` (name/phone/house/street/area/city/
        pincode match once whitespace/case is ignored). District and state
        are deliberately excluded from the match — a typo'd or corrected
        state value (e.g. "Ka" vs "Kerala") on an otherwise identical
        address should update the existing row instead of creating a new
        one, which is how repeated address entry used to silently pile up
        near-duplicate rows."""
        candidates = user.addresses.filter(
            phone=data.get("phone", ""),
            pincode=data.get("pincode", ""),
        )
        for addr in candidates:
            if (
                cls._norm(addr.full_name) == cls._norm(data.get("full_name"))
                and cls._norm(addr.house_building) == cls._norm(data.get("house") or data.get("house_building"))
                and cls._norm(addr.street) == cls._norm(data.get("street"))
                and cls._norm(addr.area) == cls._norm(data.get("area"))
                and cls._norm(addr.city) == cls._norm(data.get("city"))
            ):
                return addr
        return None
