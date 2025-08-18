# reviews/models.py

from django.db import models
from django.conf import settings


class Review(models.Model):
    """
    مدلی برای ذخیره نظرات کاربران.
    این مدل به جای ارجاع مستقیم به 'auth.User'، از 'settings.AUTH_USER_MODEL'
    استفاده می‌کند تا با مدل‌های کاربری سفارشی سازگار باشد.
    """

    # کلید خارجی به مدل کاربر فعال پروژه
    # این تغییر اصلی و مهم‌ترین بخش اصلاح شده است.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="کاربر"
    )

    # فیلد امتیاز با انتخاب بین ۱ تا ۵
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="امتیاز"
    )

    # فیلد متن نظر
    comment = models.TextField(
        verbose_name="متن نظر"
    )

    # تاریخ و زمان ثبت نظر که به صورت خودکار پر می‌شود
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    def __str__(self):
        """
        نمایش متنی آبجکت مدل در پنل ادمین و سایر بخش‌ها.
        """
        # استفاده از getattr برای دسترسی امن به فیلد نام کاربری
        username = getattr(self.user, self.user.USERNAME_FIELD, 'کاربر حذف شده')
        return f'نظر از {username} - امتیاز: {self.rating}'

    class Meta:
        """
        تنظیمات فراداده‌ای (metadata) برای مدل.
        """
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        # نظرات جدیدتر در ابتدا نمایش داده می‌شوند
        ordering = ['-created_at']





