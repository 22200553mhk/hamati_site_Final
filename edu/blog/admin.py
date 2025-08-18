from django.contrib import admin
from .models import Category, Article

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'color_code')
    # این بخش به صورت خودکار فیلد slug را از روی title پر می‌کند
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}