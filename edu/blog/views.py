from django.shortcuts import render
from .models import Category, Article
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required



@login_required
def category_list_view(request):
    # تمام دسته‌بندی‌ها را به همراه مقالات مرتبط با آن‌ها واکشی می‌کنیم
    # prefetch_related برای بهینه‌سازی کوئری دیتابیس استفاده می‌شود
    categories = Category.objects.prefetch_related('articles').all()

    context = {
        'categories': categories
    }
    return render(request, 'blog/category_list.html', context)


# blog/views.py
@login_required
def article_detail_view(request, slug):
    article = get_object_or_404(Article, slug=slug)

    # این خطوط جدید را اضافه کنید
    # مقالات دیگر در همین دسته‌بندی را پیدا کن
    # مقاله فعلی را از لیست حذف کن
    # و حداکثر ۴ مقاله را انتخاب کن
    related_articles = Article.objects.filter(category=article.category).exclude(slug=slug)[:4]

    context = {
        'article': article,
        'related_articles': related_articles  # لیست جدید را به کانتکست اضافه کن
    }
    return render(request, 'blog/article_detail.html', context)