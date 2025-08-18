from django.db import models
from django.urls import reverse

class Category(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان دسته‌بندی")
    # این فیلد برای آدرس‌دهی بهتر در URL استفاده می‌شود
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True, verbose_name="اسلاگ (نامک)")
    # این فیلد برای تعیین رنگ پس‌زمینه هر ستون استفاده می‌شود
    color_code = models.CharField(max_length=7, default="#A7C957", verbose_name="کد رنگ هگزادسیمال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['order'] # دسته‌بندی‌ها بر اساس این فیلد مرتب می‌شوند

    def __str__(self):
        return self.title


class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="articles", verbose_name="دسته‌بندی")
    title = models.CharField(max_length=255, verbose_name="عنوان مقاله")
    # این فیلد جدید را اضافه کنید
    image = models.ImageField(upload_to='articles/%Y/%m/%d/', blank=True, null=True, verbose_name="تصویر مقاله")
    content = models.TextField(verbose_name="محتوای مقاله")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, verbose_name="اسلاگ (نامک)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ['-created_at'] # مقالات جدیدتر بالاتر نمایش داده می‌شوند

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # این متد برای ساخت لینک هر مقاله استفاده می‌شود
        return reverse('article_detail', kwargs={'slug': self.slug})






