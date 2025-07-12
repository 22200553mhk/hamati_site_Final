from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import traceback


def dashboard(request):
    """داشبورد اصلی را رندر می‌کند."""
    if 'reset_data' in request.GET and 'test_results' in request.session:
        del request.session['test_results']
        request.session.modified = True
    return render(request, 'analyzer/dashboard.html')


def calculate_percentage(correct, wrong, total):
    """محاسبه درصد آزمون با احتساب نمره منفی"""
    if total == 0: return 0
    score = (correct * 3) - wrong
    max_possible_score = total * 3
    if max_possible_score == 0: return 0
    percentage = (score / max_possible_score) * 100
    return max(0, percentage)


@csrf_exempt
def save_result(request):
    """ذخیره نتایج آزمون"""
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


def get_status_text(value, thresholds):
    if value >= thresholds[2]:
        return "عالی"
    elif value >= thresholds[1]:
        return "خوب"
    elif value >= thresholds[0]:
        return "متوسط"
    else:
        return "نیازمند بهبود"


def get_fuzzy_combined_feedback(risk, efficiency, spi, pei, tue, subjects_list=None):
    # این تابع برای خلاصه بودن حذف شده، شما باید کد کامل خود را اینجا قرار دهید
    return ["این یک توصیه کلی تستی است."]


def generate_subject_feedback(subject, data):
    """تولید بازخورد شخصی‌سازی شده برای هر درس با منطق هوشمند"""
    feedback = []

    percentage = round(data.get('percentage', 0), 1)
    correct = data.get('correct', 0)
    wrong = data.get('wrong', 0)
    study_hours = data.get('study_hours', 0)
    risk = round(data.get('risk_management', 0), 1)
    productivity = round(data.get('study_productivity', 0), 1)

    # 1. تحلیل مدیریت ریسک
    if risk < 50:
        feedback.append(
            f"مدیریت ریسک {risk}% شما در {subject} با {wrong} پاسخ غلط، نشان می‌دهد که باید در انتخاب سوالات دقت بیشتری کنید.")
    else:
        feedback.append(
            f"مدیریت ریسک {risk}% شما در {subject} بسیار خوب است و نشان می‌دهد به خوبی سوالات دشوار را تشخیص می‌دهید.")

    # 2. تحلیل بهره‌وری مطالعه با منطق هوشمند
    if study_hours > 0:
        if productivity > 0:
            hours_per_percent = 1 / productivity
            feedback.append(
                f"بهره‌وری مطالعه شما {productivity} است، یعنی برای هر 1% پیشرفت حدوداً {hours_per_percent:.1f} ساعت زمان صرف کرده‌اید.")
        else:
            feedback.append(
                f"با وجود {study_hours} ساعت مطالعه، پیشرفتی در درصد شما مشاهده نشده است. پیشنهاد می‌شود روش مطالعه خود را بازبینی کنید.")
    else:  # حالت مطالعه صفر
        if percentage >= 40:
            feedback.append(
                f"شما توانسته‌اید بدون مطالعه به درصد بالا و قابل توجه {percentage:.1f}% در {subject} برسید. این نشان‌دهنده دانش پایه بسیار قوی شماست.")
        elif percentage > 0:
            feedback.append(
                f"کسب درصد {percentage:.1f}% در {subject} بدون مطالعه، نشان می‌دهد که با بخشی از مفاهیم آشنا هستید و این یک نقطه شروع خوب است.")
        else:
            feedback.append(
                f"درصد شما در {subject} بدون مطالعه صفر بوده است. این فرصت خوبی برای یک شروع تازه و قدرتمند است.")

    return feedback


def generate_report(request):
    """گزارش نهایی را با استفاده از منطق کامل تولید HTML رندر می‌کند."""
    if 'test_results' not in request.session or not request.session['test_results']:
        return HttpResponse("لطفاً ابتدا اطلاعات تست‌ها را وارد کنید.")

    test_results = request.session['test_results']
    html_output = f"<html dir='rtl'><head><title>گزارش آزمون</title><meta charset='utf-8'>"
    html_output += """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"><script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>"""
    html_output += """<script>function generatePDF(){document.getElementById("pdfButton").style.display="none";document.getElementById("loading").style.display="inline-block";const{jsPDF:e}=window.jspdf,t=new e("p","mm","a4"),d=document.getElementById("reportContent");html2canvas(d,{scale:2,useCORS:!0,logging:!1}).then(e=>{const d=210,o=295,n=e.height*d/e.width;let l=n,s=0,a=e.toDataURL("image/jpeg",1);for(t.addImage(a,"JPEG",0,s,d,n),l-=o;l>=0;)s=l-n,t.addPage(),t.addImage(a,"JPEG",0,s,d,n),l-=o;t.save("گزارش_آزمون.pdf"),document.getElementById("pdfButton").style.display="inline-block",document.getElementById("loading").style.display="none"})}</script>"""
    html_output += """<style>body{font-family:'Vazir','Tahoma',sans-serif;margin:0;padding:0;background-color:#f5f7ff;line-height:1.6;color:#333}#reportContent{background-color:#fff;box-shadow:0 5px 20px rgba(0,0,0,.1);border-radius:15px;padding:30px;margin:20px;max-width:1200px;margin-left:auto;margin-right:auto}.report-header{text-align:center;margin-bottom:30px;border-bottom:2px solid #e0e6ff;padding-bottom:20px}h1,h2,h3,h4{color:#3a36e0;font-weight:700}h1{font-size:28px;margin-bottom:10px}h2{font-size:22px;margin-top:30px;margin-bottom:15px;padding-bottom:8px;border-bottom:1px solid #e0e6ff}h3{font-size:18px;margin-top:25px;background-color:#f0f4ff;padding:10px 15px;border-radius:8px}h4{font-size:16px;margin-top:20px;color:#4361ee}table{width:100%;border-collapse:collapse;margin-bottom:25px;border-radius:10px;overflow:hidden;box-shadow:0 3px 10px rgba(0,0,0,.05)}th,td{padding:12px 15px;text-align:right}th{background:linear-gradient(135deg,#4361ee,#3a36e0);color:#fff;font-weight:700}tr:nth-child(even){background-color:#f6f8ff}tr:hover{background-color:#eef2ff}.tip{background-color:#f0f8ff;padding:15px 20px;border-right:5px solid #4361ee;margin:15px 0;border-radius:8px;box-shadow:0 3px 10px rgba(0,0,0,.05)}.chart-container{width:100%;max-width:800px;margin:30px auto;height:400px;background-color:#fff;border-radius:10px;padding:20px;box-shadow:0 3px 15px rgba(0,0,0,.08)}.button{display:inline-block;padding:12px 25px;background:linear-gradient(135deg,#4361ee,#3a36e0);color:#fff;text-decoration:none;border-radius:50px;cursor:pointer;border:none;font-family:'Vazir','Tahoma',sans-serif;font-size:14px;margin:5px}.summary-boxes{display:flex;flex-wrap:wrap;gap:20px;margin-bottom:30px}.summary-box{flex:1;min-width:200px;background:linear-gradient(135deg,#fff,#f6f8ff);border-radius:10px;padding:20px;box-shadow:0 3px 10px rgba(0,0,0,.08);text-align:center}.summary-box .value{font-size:24px;font-weight:700;color:#3a36e0;margin:10px 0}.summary-box .label{color:#666;font-size:14px}.subject-section{background-color:#fff;border-radius:10px;margin-bottom:25px;padding:20px;box-shadow:0 3px 15px rgba(0,0,0,.05)}.subject-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.subject-title{font-size:20px;color:#3a36e0;margin:0}.subject-percentage{font-size:18px;font-weight:700;color:#fff;background:linear-gradient(135deg,#4361ee,#3a36e0);padding:5px 15px;border-radius:20px}@media print{.no-print{display:none}body,#reportContent{background-color:#fff;box-shadow:none;margin:0;padding:10px}}</style></head><body>"""
    html_output += """<div class="no-print" style="text-align: center; padding: 20px;"><button id="pdfButton" class="button" onclick="generatePDF()">دانلود PDF</button><span id="loading" style="display: none;">در حال تولید...</span></div><div id="reportContent">"""
    html_output += f"""<div class="report-header"><h1>گزارش تحلیلی عملکرد آزمون</h1><p>تاریخ: {datetime.now().strftime("%Y/%m/%d")}</p></div>"""
    avg_percentage = sum(data['percentage'] for data in test_results.values()) / len(test_results)
    html_output += f"""<h2>خلاصه نتایج</h2><div class="summary-boxes"><div class="summary-box"><div class="label">تعداد دروس</div><div class="value">{len(test_results)}</div></div><div class="summary-box"><div class="label">میانگین درصد</div><div class="value">{avg_percentage:.1f}%</div></div><div class="summary-box"><div class="label">کل سوالات</div><div class="value">{sum(data['total'] for data in test_results.values())}</div></div><div class="summary-box"><div class="label">پاسخ صحیح</div><div class="value">{sum(data['correct'] for data in test_results.values())}</div></div></div>"""
    subjects = list(test_results.keys())
    percentages = [test_results[s]['percentage'] for s in subjects]
    bar_chart_data = {'labels': subjects, 'datasets': [{'label': 'درصد', 'data': percentages,
                                                        'backgroundColor': ['#4361ee', '#3a36e0', '#4cc9f0', '#4caf50',
                                                                            '#ff9800'][:len(subjects)]}]}
    html_output += f"""<h2>نمودار مقایسه درصدها</h2><div class="chart-container"><canvas id="barChart"></canvas></div><script>document.addEventListener('DOMContentLoaded',function(){{new Chart(document.getElementById('barChart').getContext('2d'),{{type:'bar',data:{json.dumps(bar_chart_data)},options:{{responsive:!0,maintainAspectRatio:!1}} }})}});</script>"""
    html_output += "<h2>تحلیل تفصیلی هر درس</h2>"
    for subject, data in test_results.items():
        html_output += f"""<div class="subject-section"><div class="subject-header"><h3 class="subject-title">درس {subject}</h3><div class="subject-percentage">{data['percentage']:.1f}%</div></div><table><tr><th>مورد</th><th>مقدار</th></tr><tr><td>تعداد سوالات</td><td>{data['total']}</td></tr><tr><td>پاسخ صحیح</td><td>{data['correct']}</td></tr><tr><td>پاسخ غلط</td><td>{data['wrong']}</td></tr><tr><td>بی‌پاسخ</td><td>{data['blank']}</td></tr></table><h4>توصیه‌های بهبود:</h4>"""
        subject_feedback = generate_subject_feedback(subject, data)
        for feedback in subject_feedback:
            html_output += f"<div class='tip'>• {feedback}</div>"
        html_output += "</div>"
    html_output += "</div></body></html>"
    return HttpResponse(html_output)