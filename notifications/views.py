import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from dg_admin.decorators import dg_admin_required

from .models import AdminNotification, PushSubscription
from .services import push_enabled, serialize


def _unread_qs(user):
    return AdminNotification.objects.exclude(read_by=user)


@ensure_csrf_cookie
@dg_admin_required
@require_GET
def poll(request):
    """Lightweight endpoint the admin bell polls every few seconds."""
    after = request.GET.get("after")
    unread_count = _unread_qs(request.user).count()
    latest = AdminNotification.objects.order_by("-id").first()
    recent = AdminNotification.objects.all()[:12]
    new_items = []
    if after and after.isdigit():
        new_items = [serialize(n, request.user) for n in AdminNotification.objects.filter(id__gt=int(after)).order_by("id")[:10]]
    return JsonResponse({
        "unread": unread_count,
        "latest_id": latest.pk if latest else 0,
        "items": [serialize(n, request.user) for n in recent],
        "new": new_items,
        "push_ready": push_enabled(),
        "vapid_public_key": settings.VAPID_PUBLIC_KEY if push_enabled() else "",
        "subscribed": PushSubscription.objects.filter(user=request.user).exists(),
    })


@dg_admin_required
@require_POST
def mark_read(request, pk):
    notification = AdminNotification.objects.filter(pk=pk).first()
    if notification:
        notification.read_by.add(request.user)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(notification.url if notification and notification.url else "notifications")


@dg_admin_required
@require_POST
def mark_all_read(request):
    through = AdminNotification.read_by.through
    ids = list(_unread_qs(request.user).values_list("id", flat=True))
    through.objects.bulk_create([through(adminnotification_id=i, user_id=request.user.pk) for i in ids], ignore_conflicts=True)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("notifications")


@dg_admin_required
def notification_list(request):
    only_unread = request.GET.get("filter") == "unread"
    qs = _unread_qs(request.user) if only_unread else AdminNotification.objects.all()
    items = [serialize(n, request.user) for n in qs[:100]]
    return render(request, "dg_admin/notifications.html", {
        "items": items, "only_unread": only_unread,
        "push_ready": push_enabled(),
        "push_count": PushSubscription.objects.filter(user=request.user).count(),
    })


@dg_admin_required
@require_POST
def push_subscribe(request):
    try:
        data = json.loads(request.body.decode() or "{}")
        endpoint = data["endpoint"]
        keys = data["keys"]
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={"user": request.user, "p256dh": keys["p256dh"], "auth": keys["auth"],
                      "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300]},
        )
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "Invalid subscription"}, status=400)
    return JsonResponse({"ok": True})


@dg_admin_required
@require_POST
def push_unsubscribe(request):
    try:
        endpoint = json.loads(request.body.decode() or "{}").get("endpoint", "")
    except ValueError:
        endpoint = ""
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


@dg_admin_required
@require_POST
def push_test(request):
    from .services import notify_admins
    notify_admins("order", "Test notification", "If you can read this, push notifications are working 🎉", "/admin/notifications/")
    return JsonResponse({"ok": True})


@require_GET
def service_worker(request):
    """The service worker lives under /admin/ so its scope covers the whole control panel."""
    js = r"""
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('push', (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { title: 'Digital Galleria', body: event.data && event.data.text() }; }
  const title = data.title || 'Digital Galleria';
  event.waitUntil(self.registration.showNotification(title, {
    body: data.body || '',
    tag: data.tag,
    icon: '/static/images/notif-icon.svg',
    badge: '/static/images/notif-icon.svg',
    data: { url: data.url || '/admin/' },
    vibrate: [120, 60, 120],
  }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/admin/';
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wins) => {
    for (const w of wins) { if (w.url.indexOf('/admin/') !== -1 && 'focus' in w) { w.navigate(url); return w.focus(); } }
    return self.clients.openWindow(url);
  }));
});
"""
    response = HttpResponse(js, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/admin/"
    response["Cache-Control"] = "no-cache"
    return response
