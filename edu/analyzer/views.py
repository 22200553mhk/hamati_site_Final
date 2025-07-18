# analyzer/views.py

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Exam, SubjectResult
import json
import jdatetime

# تابع محاسبه درصد (از کد اصلی شما)
def calculate_percentage(correct, wrong, total):
    if total == 0: return 0
    score = (correct * 3) - wrong
    max_possible_score = total * 3
    if max_possible_score == 0: return 0
    percentage = (score / max_possible_score) * 100
    return round(percentage, 2)

# تابع تولید بازخورد هوشمند (از کد اصلی شما، کاملاً دست‌نخورده)
def generate_subject_feedback(subject, data):
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
            hours_per_percent = 1 / productivity
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
        risk_ratio = wrong / (correct + wrong) * 100
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


# ----- توابع جدید برای قابلیت‌های تازه -----

def dashboard(request):
    """صفحه اصلی که قبل از شروع تحلیل جدید، سشن را پاک می‌کند."""
    if 'test_results' in request.session:
        del request.session['test_results']
    return render(request, 'analyzer/dashboard.html')


@csrf_exempt
def save_result(request):
    """نتایج را از کاربر دریافت کرده و تمام شاخص‌ها را محاسبه و در سشن ذخیره می‌کند."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            correct = int(data.get('correct', 0))
            wrong = int(data.get('wrong', 0))
            total = int(data.get('total', 0))
            study_hours = float(data.get('study_hours', 0))
            practice = int(data.get('practice', 0))

            percentage = calculate_percentage(correct, wrong, total)
            blank = total - (correct + wrong)

            # محاسبه تمام شاخص‌ها
            risk_management = (1 - (wrong / (correct + wrong))) * 100 if (correct + wrong) > 0 else 0
            denominator_ae = correct + wrong + (blank * 0.3)
            answering_efficiency = (correct / denominator_ae) * 100 if denominator_ae > 0 else 0
            study_productivity = (percentage / study_hours) * 10 if study_hours > 0 else 0
            practice_effectiveness = (percentage / practice) * 100 if practice > 0 else 0
            denominator_tue = study_hours + (practice / 20)
            time_utilization = (percentage / denominator_tue) * 10 if denominator_tue > 0 else 0

            processed_data = {
                'subject_name': data.get('subject', 'درس نامشخص'),
                'correct': correct, 'wrong': wrong, 'total': total,
                'study_hours': study_hours, 'practice': practice,
                'percentage': percentage, 'blank': blank,
                'risk_management': round(risk_management, 1),
                'answering_efficiency': round(answering_efficiency, 1),
                'study_productivity': round(study_productivity, 1),
                'practice_effectiveness': round(practice_effectiveness, 1),
                'time_utilization': round(time_utilization, 1)
            }

            if 'test_results' not in request.session:
                request.session['test_results'] = {}

            request.session['test_results'][processed_data['subject_name']] = processed_data
            request.session.modified = True
            return JsonResponse({'status': 'success', 'message': f'اطلاعات درس {processed_data["subject_name"]} با موفقیت ثبت شد.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا در پردازش داده‌ها: {e}'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'متد درخواست نامعتبر است'}, status=400)


def generate_historical_feedback(user, current_results_dict):
    """تحلیل اختصاصی برای کاربر لاگین کرده با مقایسه ۱۰ آزمون قبلی."""
    feedback = []
    # ۱۰ آزمون آخر کاربر را به همراه نتایج دروسشان واکشی می‌کنیم
    previous_exams = Exam.objects.filter(user=user).prefetch_related('subjects').order_by('-created_at')[:10]
    
    if not previous_exams:
        feedback.append("این اولین آزمونی است که ذخیره می‌کنید. برای دریافت تحلیل روند، آزمون‌های بعدی خود را نیز ذخیره کنید.")
        return feedback

    # ۱. مقایسه میانگین کل
    previous_avg_list = [exam.get_average_percentage() for exam in previous_exams if exam.get_average_percentage() > 0]
    if previous_avg_list:
        previous_avg = sum(previous_avg_list) / len(previous_avg_list)
        current_avg = sum(d['percentage'] for d in current_results_dict.values()) / len(current_results_dict)
        if current_avg > previous_avg:
            feedback.append(f"✅ **روند کلی مثبت:** میانگین درصد شما در این آزمون ({current_avg:.1f}٪) نسبت به میانگین آزمون‌های قبلی ({previous_avg:.1f}٪) **بهبود یافته است.**")
        else:
            feedback.append(f"⚠️ **نیاز به توجه:** میانگین درصد شما در این آزمون ({current_avg:.1f}٪) نسبت به آزمون‌های قبلی ({previous_avg:.1f}٪) **افت داشته است.** نقاط ضعف خود را با دقت بیشتری بررسی کنید.")

    # ۲. مقایسه درس به درس
    for subject_name, current_data in current_results_dict.items():
        past_percentages = [res.percentage for exam in previous_exams for res in exam.subjects.all() if res.subject_name == subject_name]
        if past_percentages:
            avg_past_percentage = sum(past_percentages) / len(past_percentages)
            if current_data['percentage'] > avg_past_percentage + 5: # فقط اگر تغییر معنادار بود
                feedback.append(f"🚀 **پیشرفت عالی در {subject_name}:** درصد شما ({current_data['percentage']:.1f}٪) به طور محسوسی از میانگین قبلی ({avg_past_percentage:.1f}٪) **بالاتر** است.")
            elif current_data['percentage'] < avg_past_percentage - 5:
                feedback.append(f"🔍 **بررسی درس {subject_name}:** درصد شما ({current_data['percentage']:.1f}٪) از میانگین قبلی ({avg_past_percentage:.1f}٪) **پایین‌تر** است. این درس نیاز به توجه ویژه دارد.")

    return feedback


def generate_report(request):
    """گزارش نهایی را برای کاربر مهمان و لاگین کرده، تولید می‌کند."""
    if 'test_results' not in request.session or not request.session['test_results']:
        return HttpResponse("لطفاً ابتدا اطلاعات تمام دروس را از صفحه اصلی وارد کنید.")

    test_results = request.session['test_results']
    report_items = [{'subject_name': s, 'subject_data': d, 'feedback': generate_subject_feedback(s, d)} for s, d in test_results.items()]
    
    historical_feedback = []
    is_exam_saved = False
    if request.user.is_authenticated:
        # اگر کاربر لاگین بود، تحلیل روند را برایش انجام بده
        historical_feedback = generate_historical_feedback(request.user, test_results)
        exam_id = request.session.get('saved_exam_id')
        if exam_id and Exam.objects.filter(id=exam_id, user=request.user).exists():
            is_exam_saved = True
            
    context = {
        'report_items': report_items,
        'historical_feedback': historical_feedback,
        'is_exam_saved': is_exam_saved,
    }
    return render(request, 'analyzer/report.html', context)


@login_required
@csrf_exempt
def save_exam_to_db(request):
    """این ویو فقط برای کاربران لاگین کرده است و آزمون را از سشن در دیتابیس ذخیره می‌کند."""
    if request.method == 'POST' and 'test_results' in request.session:
        if request.session.get('saved_exam_id'):
            return JsonResponse({'status': 'info', 'message': 'این آزمون قبلاً در این مرورگر ذخیره شده است.'})

        test_results = request.session['test_results']
        new_exam = Exam.objects.create(user=request.user)
        for subject, data in test_results.items():
            SubjectResult.objects.create(exam=new_exam, **data)
        
        # آیدی آزمون را در سشن ذخیره می‌کنیم تا از ذخیره مجدد با رفرش صفحه جلوگیری شود
        request.session['saved_exam_id'] = new_exam.id
        return JsonResponse({'status': 'success', 'message': 'آزمون با موفقیت در حساب کاربری شما ذخیره شد.'})
    
    return JsonResponse({'status': 'error', 'message': 'اطلاعاتی برای ذخیره یافت نشد.'}, status=400)


@login_required
def user_profile(request):
    """صفحه پروفایل کاربر که لیست ۱۰ آزمون آخر او را نمایش می‌دهد."""
    user_exams = Exam.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'analyzer/profile.html', {'exams': user_exams})