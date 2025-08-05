from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Exam, SubjectResult
import json
import jdatetime
from django.contrib.auth import logout
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
    practice = data.get('practice', 0)
    correct = data.get('correct', 0)
    wrong = data.get('wrong', 0)
    blank = data.get('blank', 0)
    total = data.get('total', 0)

    # ========== قوانین جدید شما (قوانین ۱ تا ۱۴) ==========

    # دسته اول: درصد زیر ۳۰
    if percentage < 30:
        if practice < 120:
            feedback.append(
                "درس هنوز وارد ذهن نشده. از این به بعد، قبل از زدن هر تست، اول مفاهیم رو کامل بفهم، بعد وارد تمرین شو. بدون درک، تست فقط وقته تلف کردنه.")
        else:
            feedback.append(
                "تعداد تستا خوبه، اما روش مطالعه اشتباهه. بیشتر داری اشتباهاتتو تکرار می‌کنی. باید بعد هر ۱۰ تست، یه تحلیل مفصل انجام بدی. خودتو گول نزن!")

    # دسته دوم: درصد بین ۳۰ تا ۵۰
    elif 30 <= percentage < 50:
        if practice < 120:
            feedback.append(
                "شروع خوبی نیست، ولی قابل جبرانه. فعلاً تمرکز رو بذار رو تست‌های سطح ۱ و مفاهیم پایه. از تست سنگین نترس، ولی از تست بی‌هدف دوری کن.")
        else:
            feedback.append(
                "مشخصه زحمت کشیدی، ولی گیر افتادی. راه نجات؟ تست کمتر، تحلیل بیشتر. هر غلط رو بنویس، بفهم چی شد، وگرنه تا آخر تو همین درصد می‌مونی.")

    # دسته سوم: درصد بین ۵۰ تا ۷۰
    elif 50 <= percentage < 70:
        if total > 0 and (blank / total) > 0.25:  # نزده بیشتر از یک چهارم کل سوالات
            feedback.append(
                "دانش داری، ولی اعتماد نداری! برای عبور از ۷۰ ٪  باید تصمیم‌گیریتو تقویت کنی. تمرین آزمون زمان‌دار و تکنیک رد گزینه معجزه می‌کنه.")
        elif (correct + wrong) > 0 and (wrong / (correct + wrong)) > 0.33:  # غلط بیشتر از یک سوم پاسخ‌داده‌ها
            feedback.append(
                "دقیق نیستی. یه لحظه وایسا، آروم باش. تکنیک حل مرحله به مرحله رو تمرین کن و سوال رو کامل بخون. عجله=نابودی درصد.")

    # دسته چهارم: درصد بین ۷۰ تا ۸۵
    elif 70 <= percentage < 85:
        if practice >= 120 and wrong < 5:
            feedback.append(
                "تو راه موفقیتی! فقط این روند رو تثبیت کن. هفته‌ای یه آزمون ترکیبی و مرور نکات دام‌دار، یه سکوی پرتاب می‌سازه.")
        elif total > 0 and (blank / total) > 0.25:
            feedback.append(
                "سؤالات سخت رو می‌ترسی بزنی؟ حیفه! باید رو جسارت و مدیریت زمانت کار کنی. سوالات شک‌دارو جدا کن و تو شرایط آزمون تمرینشون کن.")

    # دسته پنجم: درصد بالای ۹۰
    elif percentage >= 90:
        if practice < 120:
            feedback.append(
                "تو نابغه نیستی، ولی درس خوب بلدی. فقط مراقب باش این سطح، یه سرابه اگه تمرین ادامه پیدا نکنه. تثبیت مهم‌تر از فتحه.")
        else:
            feedback.append(
                "تبریک! الان وقتشه رو تست‌های نوآورانه و ترکیبی وقت بذاری. دنبال یه منبع قوی‌تر باش، خودتو بکش بالاتر از بقیه.")

    # قوانین کلی
    if total > 0 and (blank / total) > 0.30:
        feedback.append(
            "تو به خودت شک داری! تمرکزتو ببر روی تصمیم‌گیری سریع. تست زمان‌دار با تمرکز روی سوالای تیپ‌دار برات واجبه.")
    if total > 0 and (wrong / total) > 0.30:
        feedback.append(
            "اشتباه زیاد نشونه‌ی ضعف مفهومی یا بی‌دقتیه. اول مشخص کن کدومه. بعدش یا برگرد درسنامه، یا دقتتو با تست تشریحی بالا ببر.")
    if study_hours > 13 and percentage < 50:
        feedback.append(
            "داری وقت تلف می‌کنی. مطالعه‌ی بی‌تمرکز یا بدون تست یعنی هیچ. جلسه‌هاتو کوتاه‌تر ولی متمرکزتر کن. با تایمر بخون، نه با امید کور.")
    if study_hours < 13 and percentage >= 50:
        feedback.append(
            "این عالیه ولی موقتیه. اگه می‌خوای سطح تو حفظ کنی، مرور مستمر و افزایش تست ضروریه. کیفیت بدون کمیت نمی‌مونه.")

    # اگر هیچکدام از قوانین جدید اعمال نشد، از قوانین قدیمی استفاده کن
    if not feedback:
        if percentage >= 70:
            feedback.append(f"درصد {percentage}٪ عالی است! تسلط شما بر {subject} فوق‌العاده است.")
        elif 50 <= percentage < 70:
            feedback.append(f"درصد {percentage}٪ خیلی خوب است. با کمی تلاش بیشتر به تسلط کامل می‌رسید.")
        elif 30 <= percentage < 50:
            feedback.append(f"درصد {percentage}٪ قابل قبول است، اما جای پیشرفت زیادی در {subject} وجود دارد.")
        else:
            feedback.append(
                f"درصد {percentage}٪ پایین است. نیاز است که در درس {subject} زمان بیشتری صرف مطالعه و تمرین کنید.")

    return feedback

def home_view(request):
    """صفحه اصلی جدید سایت را رندر می‌کند."""
    return render(request, 'analyzer/home.html')



def dashboard(request):
    """داشبورد اصلی را رندر می‌کند."""
    if 'test_results' in request.session:
        del request.session['test_results']
    if 'saved_exam_id' in request.session:
        del request.session['saved_exam_id']
    request.session.modified = True
    return render(request, 'analyzer/dashboard.html')

# views.py

# views.py

def generate_historical_feedback(user, current_results_dict):
    """تحلیل اختصاصی برای کاربر لاگین کرده با مقایسه ۱۰ آزمون قبلی."""
    feedback = []
    previous_exams = Exam.objects.filter(user=user).prefetch_related('subjects').order_by('-created_at')[:10]

    if not previous_exams:
        feedback.append("این اولین آزمونی است که ذخیره می‌کنید. برای دریافت تحلیل روند، آزمون‌های بعدی خود را نیز ذخیره کنید.")
        return feedback

    for subject_name, current_data in current_results_dict.items():
        past_percentages = [res.percentage for exam in previous_exams for res in exam.subjects.all() if res.subject_name.strip() == subject_name.strip()]

        if len(past_percentages) >= 2:
            avg_past = sum(past_percentages) / len(past_percentages)
            current_percentage = current_data['percentage']

            # --- بخش اصلاح شده ---
            if current_percentage < avg_past - 20:
                feedback.append(
                    f"درس {subject_name} با افت شدید مواجه شده! درصد شما از حدود {avg_past:.0f}٪ به {current_percentage:.0f}٪ رسیده. این یک هشدار جدیه! ریشه رو پیدا کن و برگرد بالا.")
            elif current_percentage > avg_past + 20:
                feedback.append(
                    f"در درس {subject_name} رشد سریع و عالی داشتی! عالیه. همین روال رو ادامه بده، اما حواست باشه غرور تو دامته. هفته آینده فقط مرور کن، نه پرکاری.")
            else:
                # این حالت جدید اضافه شد تا عملکرد پایدار را پوشش دهد
                feedback.append(
                    f"عملکرد شما در درس {subject_name} با درصد {current_percentage:.0f}٪، نسبت به میانگین قبل ({avg_past:.0f}٪) پایدار و ثابت بوده است. این روند خوب را حفظ کنید.")
            # --- پایان بخش اصلاح شده ---
    return feedback

def generate_report(request):
    """گزارش نهایی را با آماده‌سازی داده‌ها برای قالب HTML رندر می‌کند."""
    test_results = request.session.get('test_results', {})
    if not test_results:
        messages.warning(request, "هیچ داده‌ای برای نمایش گزارش یافت نشد. لطفاً ابتدا اطلاعات آزمون را وارد کنید.")
        return redirect('dashboard')

    report_items = []
    # --- بخش اصلاح شده ---
    # از enumerate برای گرفتن شماره ردیف (i) استفاده می‌کنیم
    for i, (subject, data) in enumerate(test_results.items()):
        report_items.append({
            'subject_name': subject,
            'subject_data': data,
            'feedback': generate_subject_feedback(subject, data),
            'chart_id': i  # <<<<<< شماره ردیف به عنوان ID اضافه شد
        })
    # --- پایان بخش اصلاح شده ---

    num_subjects = len(test_results)
    avg_percentage = sum(d['percentage'] for d in test_results.values()) / num_subjects if num_subjects > 0 else 0

    historical_feedback = []
    if num_subjects > 1:
        percentages = [d['percentage'] for d in test_results.values()]
        if max(percentages) - min(percentages) > 50:
            historical_feedback.append(
                "اختلاف زیاد بین دروس وجود دارد. این یعنی تعادل نداری. تمرکزت رو از درس قوی بردار، و روزای خاصی رو فقط به درس ضعیف اختصاص بده. رشد تو از پایین‌ترین درس شروع می‌شه.")

    if request.user.is_authenticated:
        historical_feedback.extend(generate_historical_feedback(request.user, test_results))
        exam_id = request.session.get('saved_exam_id')
        is_exam_saved = exam_id and Exam.objects.filter(id=exam_id, user=request.user).exists()

        # --- بخش اصلاح شده ---
        # اگر کاربر لاگین کرده ولی هیچ فیدبک تاریخی وجود ندارد، یک پیام پیش‌فرض اضافه کن
        if not historical_feedback:
            historical_feedback.append(
                "در حال حاضر تحلیلی برای روند عملکرد شما وجود ندارد. آزمون‌های بعدی خود را ذخیره کنید.")
        # --- پایان بخش اصلاح شده ---

    else:
        is_exam_saved = False

    # ... a few lines before the context dictionary ...
    if request.user.is_authenticated:
        print(f"--- DEBUGGING FOR USER: {request.user.username} ---")
        previous_exams_count = Exam.objects.filter(user=request.user).count()
        print(f"FOUND {previous_exams_count} PREVIOUS EXAMS IN DATABASE.")
        print(f"CONTENT OF historical_feedback: {historical_feedback}")
        print("-----------------------------------------")

    context = {
        'report_items': report_items,
        'today_jalali_date': jdatetime.datetime.now().strftime("%Y/%m/%d"),
        'avg_percentage': f"{avg_percentage:.1f}",
        'total_questions': sum(d['total'] for d in test_results.values()),
        'total_correct': sum(d['correct'] for d in test_results.values()),
        'total_wrong': sum(d['wrong'] for d in test_results.values()),  # اطمینان از وجود این خط
        'subjects_list': list(test_results.keys()),
        'percentages_list': [d['percentage'] for d in test_results.values()],
        'historical_feedback': historical_feedback,
        'is_exam_saved': is_exam_saved,
    }
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
            subject_data.pop('subject_name', None)
            subject_data.pop('subject', None)
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
        response = super().form_valid(form)
        if self.request.user.is_authenticated:
            try:
                email_address = EmailAddress.objects.get(user=self.request.user, primary=True)
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
            except EmailAddress.DoesNotExist:
                EmailAddress.objects.create(
                    user=self.request.user,
                    email=self.request.user.email,
                    primary=True,
                    verified=True
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


def save_all_results(request):
    """نتایج تمام دروس را در یک درخواست واحد دریافت و در سشن ذخیره می‌کند."""
    if request.method == 'POST':
        try:
            # پاک کردن نتایج قبلی برای شروع یک آزمون جدید
            if 'test_results' in request.session:
                del request.session['test_results']
            if 'saved_exam_id' in request.session:
                del request.session['saved_exam_id']

            list_of_results = json.loads(request.body)
            processed_results = {}

            for data in list_of_results:
                correct = int(data.get('correct', 0))
                wrong = int(data.get('wrong', 0))
                total = int(data.get('total', 0))
                study_hours = float(data.get('study_hours', 0))
                practice = int(data.get('practice', 0))

                # انجام محاسبات دقیقا مانند ویو قبلی شما
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

                subject_name = data.get('subject', 'درس نامشخص')
                processed_results[subject_name] = data

            # ذخیره دیکشنری کامل در سشن
            request.session['test_results'] = processed_results
            request.session.modified = True

            return JsonResponse(
                {'status': 'success', 'message': f'اطلاعات تمام دروس با موفقیت ثبت شد.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {e}'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'متد درخواست نامعتبر است'}, status=400)
