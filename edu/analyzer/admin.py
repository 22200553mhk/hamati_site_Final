from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # استفاده از display_name به جای username
    list_display = ('display_name', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    # فیلدهای قابل ویرایش در صفحه ویرایش کاربر
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # فیلدهای اضافه شده در فرم ایجاد کاربر
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}
         ),
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # متد سفارشی برای نمایش نام یا username
    def display_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.username
    display_name.short_description = 'نام کاربر'
