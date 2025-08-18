# reviews/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Review
from .forms import ReviewForm


@login_required
def review_page(request):
    # پردازش فرم در صورت ارسال (POST)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        rating_value = request.POST.get('rating')  # گرفتن مقدار ستاره‌ها

        if form.is_valid() and rating_value:
            review = form.save(commit=False)
            review.user = request.user
            review.rating = int(rating_value)
            review.save()

            # ✅ مشکل redirect حل شد: نام URL صحیح جایگزین شد
            return redirect('reviews:review_page')

    # اگر درخواست GET بود، یک فرم خالی نمایش بده
    else:
        form = ReviewForm()

    # گرفتن نظرات قبلی کاربر برای نمایش در پایین صفحه
    user_reviews = Review.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'form': form,
        'user_reviews': user_reviews
    }

    # ✅ ویو باید همیشه یک پاسخ render برگرداند
    return render(request, 'reviews/review_page.html', context)  # نام تمپلیت خود را اینجا قرار دهید


@login_required
def delete_review(request, review_id):
    # استفاده از get به جای filter().first() برای مدیریت بهتر خطای 404 (اختیاری اما بهتر)
    try:
        review = Review.objects.get(id=review_id, user=request.user)
        review.delete()
    except Review.DoesNotExist:
        pass  # یا هر منطق دیگری برای زمانی که نظر پیدا نشد
    return redirect('reviews:review_page')


@login_required
def delete_all_reviews(request):
    Review.objects.filter(user=request.user).delete()
    return redirect('reviews:review_page')