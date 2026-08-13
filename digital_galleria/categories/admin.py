from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active', 'display_order')
    list_filter = ('active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('display_order', 'active')
