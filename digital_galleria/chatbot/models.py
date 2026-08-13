from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    keywords = models.CharField(max_length=255, blank=True, help_text='Comma separated keywords used for matching')
    priority = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-priority']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class ChatConversation(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='chat_conversations')
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-updated_at']
    def __str__(self):
        return f"{self.user.display_name} — {self.title or 'Conversation'}"

class ChatMessage(models.Model):
    ROLE_CHOICES = (('user','User'),('assistant','Assistant'),('admin','Admin'))
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f"{self.role}: {self.content[:60]}"
