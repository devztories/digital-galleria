from django.conf import settings
from django.db import models


class AdminNotification(models.Model):
    """One in-app notification shown to every admin (bell icon + Notifications page).

    Notifications are shared by the whole admin team — `read_by` tracks who has
    seen each one, so one admin reading it doesn't hide it from the others.
    """
    KIND_CHOICES = [
        ("order", "New order"),
        ("payment", "Payment"),
        ("customization", "Customization"),
        ("chat", "Chat"),
        ("stock", "Stock"),
        ("customer", "Customer"),
    ]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="order")
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=400, blank=True)
    url = models.CharField(max_length=300, blank=True, help_text="Admin page to open when clicked.")
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="read_notifications")
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_date", "-id"]

    def __str__(self):
        return self.title


class PushSubscription(models.Model):
    """A browser/device an admin has allowed web-push on."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=300, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} · {self.endpoint[:40]}…"
