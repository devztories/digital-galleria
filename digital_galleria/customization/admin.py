from django.contrib import admin
from django.utils.html import format_html
from .models import Customization, CustomizationImage


class CustomizationImageInline(admin.TabularInline):
    model = CustomizationImage
    extra = 0
    readonly_fields = ('original_filename', 'file_size', 'content_type', 'width', 'height', 'uploaded_at', 'download_original')
    fields = ('original_file', 'download_original', 'original_filename', 'file_size', 'content_type', 'width', 'height', 'uploaded_at')
    def download_original(self, obj):
        if not obj or not obj.original_file:
            return '-'
        return format_html('<a href="{}" download class="button">Download Original</a>', obj.original_file.url)
    download_original.short_description = 'Original download'


@admin.register(Customization)
class CustomizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'recipient_name', 'via_whatsapp', 'created_at')
    list_filter = ('via_whatsapp',)
    inlines = [CustomizationImageInline]
