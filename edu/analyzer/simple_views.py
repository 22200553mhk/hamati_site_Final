from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import jdatetime
from datetime import datetime


def dashboard(request):
    """داشبورد اصلی را رندر می‌کند و داده‌های قبلی را پاک می‌کند."""
    if 'test_results' in request.session:
        del request.session['test_results']
        request.session.modified = True
    return render(request, 'analyzer/dashboard.html')


def calculate_percentage(correct, wrong, total):
    """محاسبه درصد آزمون با نمره منفی (از -33.3 تا 100)."""
    if total == 0:
        return 0
    score = (correct * 3) - wrong
    max_possible_score = total * 3
    if max_possible_score == 0:
        return 0
    percentage = (score / max_possible_score) * 100
    return round(percentage, 2)


@csrf_exempt
def save_result(request):
    """ذخیره نتایج آزمون در سشن."""
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


def generate_subject_feedback(subject, data):
    """تولید بازخورد تحلیلی برای هر درس."""
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


def generate_report(request):
    """ایجاد و رندر گزارش نهایی."""
    if 'test_results' not in request.session or not request.session['test_results']:
        return HttpResponse("لطفاً ابتدا اطلاعات تمام دروس را از صفحه اصلی وارد کنید.")

    test_results = request.session['test_results']

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

        # داده‌ها برای جاوااسکریپت به صورت امن ارسال می‌شوند
        'subjects': list(test_results.keys()),
        'percentages': [d['percentage'] for d in test_results.values()],
    }

    return render(request, 'analyzer/report.html', context)
