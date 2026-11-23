from django.db import models


class AuditLog(models.Model):
    admin_user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    target = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return f"{self.admin_user} - {self.action}"


def log_action(request, action, target=""):
    AuditLog.objects.create(admin_user=request.user, action=action, target=target)
