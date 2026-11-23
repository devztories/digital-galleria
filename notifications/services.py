"""Create admin notifications and fan them out as web-push messages."""
import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import AdminNotification, PushSubscription

logger = logging.getLogger(__name__)

KIND_ICONS = {"order": "🛒", "payment": "💳", "customization": "🎨", "chat": "💬", "stock": "📦", "customer": "👤"}


def push_enabled():
    return bool(getattr(settings, "VAPID_PUBLIC_KEY", "") and getattr(settings, "VAPID_PRIVATE_KEY", ""))


def _send_push(notification):
    if not push_enabled():
        return
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:  # pywebpush not installed — in-app bell still works
        logger.warning("pywebpush is not installed; skipping push delivery")
        return

    payload = json.dumps({
        "title": notification.title,
        "body": notification.body,
        "url": notification.url or "/admin/",
        "tag": f"dg-{notification.kind}-{notification.pk}",
        "kind": notification.kind,
    })
    admin_ids = get_user_model().objects.filter(is_active=True, is_staff=True).values_list("id", flat=True)
    for sub in PushSubscription.objects.filter(user_id__in=list(admin_ids)):
        try:
            webpush(
                subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
                timeout=5,
            )
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):  # subscription expired / unsubscribed — clean it up
                sub.delete()
            else:
                logger.warning("Push failed for subscription %s: %s", sub.pk, exc)
        except Exception as exc:  # never let a push problem break an order or payment
            logger.warning("Push failed for subscription %s: %s", sub.pk, exc)


def notify_admins(kind, title, body="", url=""):
    """Record a notification and push it to every subscribed admin device.

    Safe to call from anywhere: failures are logged, never raised, and the push
    is sent only after the surrounding DB transaction has committed.
    """
    try:
        notification = AdminNotification.objects.create(kind=kind, title=title[:200], body=body[:400], url=url[:300])
    except Exception as exc:
        logger.warning("Could not create admin notification: %s", exc)
        return None
    transaction.on_commit(lambda: _send_push(notification))
    return notification


def serialize(notification, user=None):
    from django.utils import timezone
    from django.utils.timesince import timesince
    unread = True
    if user is not None:
        unread = not notification.read_by.filter(pk=user.pk).exists()
    return {
        "id": notification.pk,
        "kind": notification.kind,
        "icon": KIND_ICONS.get(notification.kind, "🔔"),
        "title": notification.title,
        "body": notification.body,
        "url": notification.url or "/admin/",
        "unread": unread,
        "time": timesince(notification.created_date, timezone.now()) + " ago",
    }
