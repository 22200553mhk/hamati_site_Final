# reviews/admin.py
from django.contrib import admin
from .models import Review
import jdatetime


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # ✅ 'user' را با متد جدید 'user_full_name' جایگزین کردیم
    list_display = ('user_full_name', 'rating', 'comment', 'jalali_created_at')
    list_filter = ('rating', 'created_at')

    # ✅ فیلدهای جستجو را به‌روز کردیم تا بر اساس نام و نام خانوادگی هم جستجو کند
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'comment')

    def jalali_created_at(self, obj):
        if obj.created_at:
            # توجه: مطمئن شوید jdatetime را به درستی import کرده‌اید
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime("%Y/%m/%d - %H:%M")
        return "-"

    jalali_created_at.short_description = "تاریخ ثبت"

    # ✅ این متد جدید برای نمایش نام کامل کاربر است
    def user_full_name(self, obj):
        # ابتدا تلاش می‌کنیم نام کامل کاربر را از متد داخلی جنگو بگیریم
        full_name = obj.user.get_full_name()
        # اگر نام کامل وجود داشت، آن را نمایش می‌دهیم
        if full_name:
            return full_name
        # در غیر این صورت (مثلاً برای کاربران عادی)، همان نام کاربری را نمایش می‌دهیم
        return obj.user.username

    # عنوان ستون در پنل ادمین را مشخص می‌کنیم
    user_full_name.short_description = 'نام کاربر'