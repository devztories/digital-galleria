from django.db import models


class ChatConversation(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, null=True, blank=True, related_name="chats")
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_date"]


class ChatMessage(models.Model):
    ATTACHMENT_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
    ]
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("bot", "Hopy")])
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to="chat/", blank=True, null=True)
    attachment_type = models.CharField(max_length=10, choices=ATTACHMENT_TYPES, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    # Backwards compatibility with the existing image field/data.
    reference_image = models.ImageField(upload_to="chat/", blank=True, null=True)

    @property
    def attachment_url(self):
        field = self.attachment or self.reference_image
        try:
            return field.url if field else ""
        except ValueError:
            return ""

    @property
    def attachment_name(self):
        return self.original_filename or (
            self.reference_image.name.rsplit("/", 1)[-1] if self.reference_image else ""
        )
