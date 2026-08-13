from django.contrib import admin
from .models import FAQ, ChatConversation, ChatMessage

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'priority', 'active')
    list_editable = ('priority', 'active')
    search_fields = ('question', 'keywords')

@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('user','title','created_at','updated_at')
    search_fields = ('user__username','user__name','user__email','title')
    list_filter = ('created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation','role','created_at')
    search_fields = ('content','conversation__user__username','conversation__user__name')
    list_filter = ('role','created_at')
