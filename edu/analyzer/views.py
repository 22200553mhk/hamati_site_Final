from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Exam, SubjectResult
import json
import jdatetime
from django.contrib.auth import logout

# ایمپورت‌های جدید و کامل شده
import socket
from django.contrib import messages
from allauth.account.views import SignupView, LoginView
from allauth.account.models import EmailAddress


# ===================================================================
# تمام کدهای اصلی و دست‌نخورده شما
# ===================================================================

def calculate_percentage(correct, wrong, total):
    """محاسبه درصد آزمون با احتساب نمره منفی (از -33.3 تا 100)."""
    if total == 0: return 0
    score = (correct * 3) - wrong
    max_possible_score = total * 3
    if max_possible_score == 0: return 0
    percentage = (score / max_possible_score) * 100
    return round(percentage, 2)


def generate_subject_feedback(subject, data):
    """بازخورد هوشمند برای هر درس تولید می‌کند."""
    feedback = []
    percentage = round(data.get('percentage', 0), 1)
    study_hours = data.get('study_hours', 0)
    productivity = round(data.get('study_productivity', 0), 1)
    practice = data.get('practice', 0)
    correct = data.get('correct', 0)
    wrong = data.get('wrong', 0)
    blank = data.get('blank', 0)

    if study_hours > 0:
        if productivity > 0:
            hours_per_percent = 1 / productivity if productivity != 0 else 0
            feedback.append(
                f"بهره‌وری مطالعه شما {productivity} است، یعنی برای هر ۱٪ پیشرفت حدوداً {hours_per_percent:.1f} ساعت زمان صرف کرده‌اید.")
        else:
            feedback.append(
                f"با وجود {study_hours} ساعت مطالعه، پیشرفتی در درصد شما مشاهده نشده است. پیشنهاد می‌شود روش مطالعه خود را بازبینی کنید.")
    else:
        if percentage >= 40:
            feedback.append(
                f"شما توانسته‌اید بدون مطالعه به درصد بالا و قابل توجه {percentage:.1f}٪ در {subject} برسید. این نشان‌دهنده دانش پایه بسیار قوی شماست.")
        elif percentage > 0:
            feedback.append(
                f"کسب درصد {percentage:.1f}٪ در {subject} بدون مطالعه، نشان می‌دهد که با بخشی از مفاهیم آشنا هستید و این یک نقطه شروع خوب است.")
        else:
            feedback.append(
                f"درصد شما در {subject} بدون مطالعه صفر بوده است. این فرصت خوبی برای یک شروع تازه و قدرتمند است.")

    if wrong > 0:
        risk_ratio = wrong / (correct + wrong) * 100 if (correct + wrong) > 0 else 0
        if risk_ratio > 30:
            feedback.append(
                f"نسبت پاسخ‌های غلط به کل پاسخ‌های داده شده ({risk_ratio:.1f}%) بالا است. پیشنهاد می‌شود در تست‌زنی دقت بیشتری داشته باشید.")
        else:
            feedback.append(
                f"مدیریت ریسک شما قابل قبول است (نسبت پاسخ غلط: {risk_ratio:.1f}%). ادامه این روند می‌تواند مفید باشد.")
    else:
        if correct > 0:
            feedback.append(
                "هیچ پاسخ غلطی نداشته‌اید! این نشان‌دهنده دقت بالا و تسلط خوب شما بر مباحث است.")

    if practice > 0:
        effectiveness = round(data.get('practice_effectiveness', 0), 1)
        if effectiveness > 5:
            feedback.append(
                f"تست‌های تمرینی شما مؤثر بوده‌اند اثربخشی: {effectiveness}. تعداد مناسب تست‌ها را حفظ کنید.")
        else:
            feedback.append(
                f"اثربخشی تست‌های تمرینی شما پایین است ({effectiveness}). کیفیت تست‌زنی را افزایش دهید.")
    else:
        feedback.append(
            "هیچ تست تمرینی ثبت نشده است. حل تست‌های متنوع می‌تواند به بهبود عملکرد کمک کند.")

    return feedback


def dashboard(request):
    """داشبورد اصلی را رندر می‌کند و سشن را برای تحلیل جدید پاک‌سازی می‌کند."""
    # پاک کردن نتایج آزمون قبلی
    if 'test_results' in request.session:
        del request.session['test_results']

    # ========== کد جدید برای حل مشکل دکمه ذخیره ==========
    # پاک کردن یادداشت مربوط به ذخیره شدن آزمون قبلی
    if 'saved_exam_id' in request.session:
        del request.session['saved_exam_id']
    # ====================================================

    request.session.modified = True
    return render(request, 'analyzer/dashboard.html')


@csrf_exempt
def save_result(request):
    """نتایج آزمون را از کاربر دریافت، پردازش و در سشن ذخیره می‌کند."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            correct = int(data.get('correct', 0))
            wrong = int(data.get('wrong', 0))
            total = int(data.get('total', 0))
            study_hours = float(data.get('study_hours', 0))
            practice = int(data.get('practice', 0))

            data['percentage'] = calculate_percentage(correct, wrong, total)
            data['blank'] = total - (correct + wrong)

            risk_management = (1 - (wrong / (total - data['blank']))) * 100 if (total - data['blank']) > 0 else 0
            denominator_ae = correct + wrong + (data['blank'] * 0.3)
            answering_efficiency = (correct / denominator_ae) * 100 if denominator_ae > 0 else 0
            study_productivity = (data['percentage'] / study_hours) * 10 if study_hours > 0 else 0
            practice_effectiveness = (data['percentage'] / practice) * 100 if practice > 0 else 0
            denominator_tue = study_hours + (practice / 20)
            time_utilization = (data['percentage'] / denominator_tue) * 10 if denominator_tue > 0 else 0

            data.update({
                'risk_management': round(risk_management, 1),
                'answering_efficiency': round(answering_efficiency, 1),
                'study_productivity': round(study_productivity, 1),
                'practice_effectiveness': round(practice_effectiveness, 1),
                'time_utilization': round(time_utilization, 1)
            })

            if 'test_results' not in request.session:
                request.session['test_results'] = {}

            subject = data.get('subject', 'درس نامشخص')
            request.session['test_results'][subject] = data
            request.session.modified = True

            return JsonResponse(
                {'status': 'success', 'message': f'اطلاعات درس <strong>{subject}</strong> با موفقیت ثبت شد.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {e}'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'متد درخواست نامعتبر است'}, status=400)


def generate_historical_feedback(user, current_results_dict):
    """تحلیل اختصاصی برای کاربر لاگین کرده با مقایسه ۱۰ آزمون قبلی."""
    feedback = []
    previous_exams = Exam.objects.filter(user=user).prefetch_related('subjects').order_by('-created_at')[:10]

    if not previous_exams:
        feedback.append(
            "این اولین آزمونی است که ذخیره می‌کنید. برای دریافت تحلیل روند، آزمون‌های بعدی خود را نیز ذخیره کنید.")
        return feedback

    previous_avg_list = [exam.get_average_percentage() for exam in previous_exams if exam.get_average_percentage() > 0]
    if previous_avg_list:
        previous_avg = sum(previous_avg_list) / len(previous_avg_list)
        current_avg = sum(d['percentage'] for d in current_results_dict.values()) / len(current_results_dict)
        if current_avg > previous_avg:
            feedback.append(
                f"✅ **روند کلی مثبت:** میانگین درصد شما در این آزمون ({current_avg:.1f}٪) نسبت به میانگین آزمون‌های قبلی ({previous_avg:.1f}٪) **بهبود یافته است.**")
        else:
            feedback.append(
                f"⚠️ **نیاز به توجه:** میانگین درصد شما در این آزمون ({current_avg:.1f}٪) نسبت به آزمون‌های قبلی ({previous_avg:.1f}٪) **افت داشته است.**")

    for subject_name, current_data in current_results_dict.items():
        past_percentages = [res.percentage for exam in previous_exams for res in exam.subjects.all() if
                            res.subject_name == subject_name]
        if past_percentages:
            avg_past_percentage = sum(past_percentages) / len(past_percentages)
            if current_data['percentage'] > avg_past_percentage + 5:
                feedback.append(
                    f"🚀 **پیشرفت عالی در {subject_name}:** درصد شما ({current_data['percentage']:.1f}٪) به طور محسوسی از میانگین قبلی ({avg_past_percentage:.1f}٪) **بالاتر** است.")
            elif current_data['percentage'] < avg_past_percentage - 5:
                feedback.append(
                    f"🔍 **بررسی درس {subject_name}:** درصد شما ({current_data['percentage']:.1f}٪) از میانگین قبلی ({avg_past_percentage:.1f}٪) **پایین‌تر** است.")
    return feedback


def generate_report(request):
    """گزارش نهایی را با آماده‌سازی داده‌ها برای قالب HTML رندر می‌کند."""
    test_results = request.session.get('test_results', {})

    if not test_results:
        messages.warning(request, "هیچ داده‌ای برای نمایش گزارش یافت نشد. لطفاً ابتدا اطلاعات آزمون را وارد کنید.")
        return redirect('dashboard')

    report_items = []
    for subject, data in test_results.items():
        report_items.append({
            'subject_name': subject,
            'subject_data': data,
            'feedback': generate_subject_feedback(subject, data)
        })

    num_subjects = len(test_results)
    avg_percentage = sum(d['percentage'] for d in test_results.values()) / num_subjects if num_subjects > 0 else 0

    context = {
        'report_items': report_items,
        'today_jalali_date': jdatetime.datetime.now().strftime("%Y/%m/%d"),
        'avg_percentage': f"{avg_percentage:.1f}",
        'total_questions': sum(d['total'] for d in test_results.values()),
        'total_correct': sum(d['correct'] for d in test_results.values()),
        'subjects_list': list(test_results.keys()),
        'percentages_list': [d['percentage'] for d in test_results.values()],
    }

    if request.user.is_authenticated:
        context['historical_feedback'] = generate_historical_feedback(request.user, test_results)
        exam_id = request.session.get('saved_exam_id')
        context['is_exam_saved'] = exam_id and Exam.objects.filter(id=exam_id, user=request.user).exists()

    return render(request, 'analyzer/report.html', context)


@login_required
@csrf_exempt
def save_exam_to_db(request):
    """
    آزمون را از سشن در دیتابیس ذخیره می‌کند.
    اگر کاربر ۱۰ آزمون داشته باشد، قدیمی‌ترین را حذف می‌کند.
    """
    if request.method == 'POST' and 'test_results' in request.session:
        user = request.user
        exam_count = Exam.objects.filter(user=user).count()
        if exam_count >= 10:
            oldest_exam = Exam.objects.filter(user=user).order_by('created_at').first()
            if oldest_exam:
                oldest_exam.delete()

        test_results = request.session['test_results']
        new_exam = Exam.objects.create(user=user)
        for subject, data in test_results.items():
            subject_data = data.copy()
            # ========== اصلاح نهایی برای رفع باگ ==========
            subject_data.pop('subject', None)
            # ============================================
            SubjectResult.objects.create(exam=new_exam, subject_name=subject, **subject_data)

        request.session['saved_exam_id'] = new_exam.id
        request.session.modified = True
        return JsonResponse({'status': 'success', 'message': 'آزمون با موفقیت در حساب کاربری شما ذخیره شد.'})

    return JsonResponse({'status': 'error', 'message': 'اطلاعاتی برای ذخیره یافت نشد.'}, status=400)


@login_required
def user_profile(request):
    """صفحه پروفایل کاربر با لیست آزمون‌های ذخیره شده."""
    user_exams = Exam.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'analyzer/profile.html', {'exams': user_exams})


@login_required
def delete_account(request):
    """حذف حساب کاربری."""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('dashboard')

    return render(request, 'analyzer/delete_account_confirm.html')


@login_required
def account_redirect(request):
    """ویو نگهبان برای مدیریت ریدایرکت پس از ورود."""
    is_verified = request.user.emailaddress_set.filter(primary=True, verified=True).exists()
    if is_verified:
        return redirect('user_profile')
    else:
        messages.warning(request,
                         'حساب کاربری شما هنوز فعال نشده است. لطفاً ایمیل خود را برای لینک فعال‌سازی بررسی کنید.')
        logout(request)
        return redirect('account_login')


# --- ویوهای سفارشی برای حل مشکلات allauth ---

class CustomSignupView(SignupView):
    """ویو سفارشی برای مدیریت خطای ارسال ایمیل در زمان ثبت‌نام."""

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except socket.gaierror:
            messages.error(self.request,
                           "خطا در اتصال به سرور ایمیل. لطفاً از اتصال اینترنت خود اطمینان حاصل کرده و مجدداً تلاش کنید.")
            return self.form_invalid(form)


class CustomLoginView(LoginView):
    """ویو سفارشی برای حل مشکل چرخه تایید ایمیل در زمان ورود."""

    def form_valid(self, form):
        # ابتدا اجازه می‌دهیم فرآیند اصلی ورود به طور کامل انجام شود
        response = super().form_valid(form)

        # حالا که کاربر به طور کامل وارد شده (self.request.user یک کاربر واقعی است)،
        # وضعیت ایمیل او را چک و در صورت نیاز تصحیح می‌کنیم.
        # این کد فقط برای کاربرانی اجرا می‌شود که `is_authenticated` هستند.
        if self.request.user.is_authenticated:
            try:
                email_address = EmailAddress.objects.get(user=self.request.user, primary=True)
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
            except EmailAddress.DoesNotExist:
                # اگر کاربر ایمیلی در مدل EmailAddress نداشته باشد (مثلا کاربر قدیمی)،
                # می‌توانیم یکی برای او بسازیم.
                EmailAddress.objects.create(
                    user=self.request.user,
                    email=self.request.user.email,
                    primary=True,
                    verified=True  # فرض می‌کنیم اگر توانسته با رمز وارد شود، ایمیل معتبر است
                )

        return response


@login_required
def delete_single_exam(request, exam_id):
    if request.method == 'POST':
        exam = Exam.objects.filter(pk=exam_id, user=request.user).first()
        if exam:
            exam.delete()
            messages.success(request, "آزمون با موفقیت حذف شد.")
        else:
            messages.error(request, "شما اجازه حذف این آزمون را ندارید.")
    return redirect('user_profile')

@login_required
def delete_all_exams(request):
    if request.method == 'POST':
        Exam.objects.filter(user=request.user).delete()
        messages.success(request, "تمام آزمون‌های شما با موفقیت حذف شدند.")
    return redirect('user_profile')