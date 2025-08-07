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

    if percentage < 30:
        if practice < 120:
            feedback.append(
                "درس هنوز وارد ذهن نشده. از این به بعد، قبل از زدن هر تست، اول مفاهیم رو کامل بفهم، بعد وارد تمرین شو. بدون درک، تست فقط وقته تلف کردنه.")
        else:
            feedback.append(
                "تعداد تستا خوبه، اما روش مطالعه اشتباهه. بیشتر داری اشتباهاتتو تکرار می‌کنی. باید بعد هر ۱۰ تست، یه تحلیل مفصل انجام بدی. خودتو گول نزن!")
    elif 30 <= percentage < 50:
        if practice < 120:
            feedback.append(
                "شروع خوبی نیست، ولی قابل جبرانه. فعلاً تمرکز رو بذار رو تست‌های سطح ۱ و مفاهیم پایه. از تست سنگین نترس، ولی از تست بی‌هدف دوری کن.")
        else:
            feedback.append(
                "مشخصه زحمت کشیدی، ولی گیر افتادی. راه نجات؟ تست کمتر، تحلیل بیشتر. هر غلط رو بنویس، بفهم چی شد، وگرنه تا آخر تو همین درصد می‌مونی.")
    elif 50 <= percentage < 70:
        if total > 0 and (blank / total) > 0.25:
            feedback.append(
                "دانش داری، ولی اعتماد نداری! برای عبور از ۷۰ ٪  باید تصمیم‌گیریتو تقویت کنی. تمرین آزمون زمان‌دار و تکنیک رد گزینه معجزه می‌کنه.")
        elif (correct + wrong) > 0 and (wrong / (correct + wrong)) > 0.33:
            feedback.append(
                "دقیق نیستی. یه لحظه وایسا، آروم باش. تکنیک حل مرحله به مرحله رو تمرین کن و سوال رو کامل بخون. عجله=نابودی درصد.")
    elif 70 <= percentage < 85:
        if practice >= 120 and wrong < 5:
            feedback.append(
                "تو راه موفقیتی! فقط این روند رو تثبیت کن. هفته‌ای یه آزمون ترکیبی و مرور نکات دام‌دار، یه سکوی پرتاب می‌سازه.")
        elif total > 0 and (blank / total) > 0.25:
            feedback.append(
                "سؤالات سخت رو می‌ترسی بزنی؟ حیفه! باید رو جسارت و مدیریت زمانت کار کنی. سوالات شک‌دارو جدا کن و تو شرایط آزمون تمرینشون کن.")
    elif percentage >= 90:
        if practice < 120:
            feedback.append(
                "تو نابغه نیستی، ولی درس خوب بلدی. فقط مراقب باش این سطح، یه سرابه اگه تمرین ادامه پیدا نکنه. تثبیت مهم‌تر از فتحه.")
        else:
            feedback.append(
                "تبریک! الان وقتشه رو تست‌های نوآورانه و ترکیبی وقت بذاری. دنبال یه منبع قوی‌تر باش، خودتو بکش بالاتر از بقیه.")

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
    return render(request, 'analyzer/home.html')


def dashboard(request):
    if 'test_results' in request.session:
        del request.session['test_results']
    if 'saved_exam_id' in request.session:
        del request.session['saved_exam_id']
    request.session.modified = True
    return render(request, 'analyzer/dashboard.html')


def generate_historical_feedback(user, current_results_dict):
    feedback = []
    if Exam.objects.filter(user=user).count() == 0:
        return []

    previous_exams = Exam.objects.filter(user=user).prefetch_related('subjects').order_by('-created_at')[:10]
    has_comparison = False
    for subject_name, current_data in current_results_dict.items():
        past_percentages = [res.percentage for exam in previous_exams for res in exam.subjects.all() if
                            res.subject_name.strip() == subject_name.strip()]
        if len(past_percentages) >= 2:
            has_comparison = True
            avg_past = sum(past_percentages) / len(past_percentages)
            current_percentage = current_data['percentage']
            if current_percentage < avg_past - 20:
                feedback.append(
                    f"درس {subject_name} با افت شدید مواجه شده! درصد شما از حدود {avg_past:.0f}٪ به {current_percentage:.0f}٪ رسیده. این یک هشدار جدیه! ریشه رو پیدا کن و برگرد بالا.")
            elif current_percentage > avg_past + 20:
                feedback.append(
                    f"در درس {subject_name} رشد سریع و عالی داشتی! عالیه. همین روال رو ادامه بده، اما حواست باشه غرور تو دامته. هفته آینده فقط مرور کن، نه پرکاری.")
            else:
                feedback.append(
                    f"عملکرد شما در درس {subject_name} با درصد {current_percentage:.0f}٪، نسبت به میانگین قبل ({avg_past:.0f}٪) پایدار و ثابت بوده است. این روند خوب را حفظ کنید.")

    if not has_comparison and Exam.objects.filter(user=user).exists():
        feedback.append("برای دریافت تحلیل روند مقایسه‌ای، حداقل دو آزمون را ذخیره کنید.")

    return feedback


def generate_complementary_feedback(test_results):
    feedback = {}
    percentages = {name: data['percentage'] for name, data in test_results.items()}
    normalized_percentages = {
        'ریاضی': percentages.get('ریاضی'),
        'فیزیک': percentages.get('فیزیک'),
        'شیمی': percentages.get('شیمی'),
        'زیست': percentages.get('زیست‌شناسی')
    }
    normalized_percentages = {k: v for k, v in normalized_percentages.items() if v is not None}

    if len(normalized_percentages) < 4:
        feedback["تحلیل جامع سطح عملکرد"] = [
            "برای دریافت تحلیل جامع و توصیه‌های تکمیلی، لطفاً نتایج هر چهار درس را وارد کنید."]
        return feedback

    p = normalized_percentages
    all_perc = list(p.values())

    cat1_feedback = []
    if p.get('ریاضی', 0) > 90 and p.get('فیزیک', 100) < 50:
        cat1_feedback.append(
            "<strong>تشخیص دقیق وضعیت ریاضی-فیزیک:</strong> تحلیل نمرات شما یک تفاوت واضح بین دروس زوج محاسباتی، یعنی ریاضی و فیزیک، را نشان می‌دهد. این وضعیت به ما می‌گوید که شما به احتمال زیاد از **درک محاسباتی** بسیار خوبی برخوردار هستید که باعث شده نمره ریاضی شما عالی باشد، اما در مقابل، **فهم فیزیکی** شما که به درک مفهومی-کاربردی مسائل مربوط می‌شود، ضعیف است. این یک نکته کلیدی است: مشکل شما در فیزیک، محاسبات آن نیست، بلکه درک عمیق مفاهیم است.")
        cat1_feedback.append(
            "<strong>راهکار استراتژیک (استفاده از نقطه قوت و تغییر تمرکز):</strong> این که ریاضی شما قوی است یک نقطه قوت بسیار بزرگ محسوب می‌شود، زیرا محاسبات قوی یک ابزار کلیدی برای موفقیت در فیزیک است. بنابراین، استراتژی اصلی شما باید این باشد که از این نقطه قوت استفاده کرده و تمام تمرکز خود را روی ضعف اصلی، یعنی فهم مفاهیم، بگذارید. برای این منظور، فعلاً باید حجم تست‌های صرفاً محاسباتی فیزیک را کاهش داده و در مقابل، زمان بسیار بیشتری را به حل و تحلیل تست‌های **مفهومی** اختصاص دهید تا این بخش از دانش خود را تقویت کنید.")
        cat1_feedback.append(
            "<strong>برنامه عملیاتی (بازسازی پایه و یادگیری عمیق):</strong> برای اجرای موفق این استراتژی، باید مطمئن شوید که پایه فیزیک شما قوی است. هر مبحثی را که احساس می‌کنید از پایه متوجه نشده‌اید، شناسایی کرده و با صبر و حوصله از ابتدا مطالعه کنید. بهترین روش برای این کار، استفاده از **آموزش‌های تصویری یا کلاس‌های حضوری** است تا بتوانید مفاهیم را به صورت شهودی و عمیق یاد بگیرید و از حفظ کردن صرف فرمول‌ها پرهیز کنید.")

    if p.get('فیزیک', 0) > 90 and p.get('ریاضی', 100) < 50:
        cat1_feedback.append(
            "<strong>تشخیص دقیق وضعیت فیزیک-ریاضی:</strong> شما قدرت تحلیل پدیده‌های فیزیکی بسیار خوبی دارید که نقطه قوت شما در فیزیک است، اما در مقابل، در **محاسبات یا ریاضی پایه** ضعف جدی نشان می‌دهید. این یعنی باید روی ابزارهای ریاضی خود که پیش‌نیاز فیزیک هستند، به طور ویژه کار کنید.")
        cat1_feedback.append(
            "<strong>راهکار استراتژیک (بازسازی پایه ریاضی):</strong> بهترین کار در این موقعیت، بازگشت و کار روی مباحث پایه‌ای ریاضی است. دروسی را که از ابتدا به خوبی یاد نگرفته‌اید شناسایی کرده و با استفاده از ویدیو آموزشی یا کتاب، آن‌ها را به طور کامل بازآموزی کنید تا ضعف محاسباتی شما به طور کامل جبران شود.")
        cat1_feedback.append(
            "<strong>برنامه عملیاتی (تمرین ترکیبی و هدفمند):</strong> پس از تقویت پایه ریاضی، تمرکز خود را در تست‌های فیزیک، روی تست‌هایی قرار دهید که **محاسبات سنگین‌تری** دارند. این کار یک تیر و دو نشان است: هم ریاضی شما را به صورت کاربردی تقویت می‌کند و هم کیفیت و تسلط شما را در فیزیک تثبیت می‌نماید.")

    if p.get('زیست', 0) > 90 and p.get('شیمی', 100) < 50:
        cat1_feedback.append(
            "<strong>تشخیص دقیق وضعیت زیست-شیمی:</strong> شما مهارت مطالعه متنی و حفظی بسیار خوبی دارید که در درس زیست به شما کمک کرده است، اما در مقابل، در **درک ساختارهای شیمیایی و مفاهیم واکنشی** که نیازمند تحلیل عمیق‌تر هستند، ضعف دارید.")
        cat1_feedback.append(
            "<strong>راهکار استراتژیک (یادگیری مفهومی شیمی):</strong> اولین و مهم‌ترین گام برای شما، یادگیری مفهومی و پایه‌ای شیمی است. توصیه می‌شود با استفاده از ویدیوهای آموزشی، تمام مفاهیم پایه شیمی، به خصوص مباحثی مانند جدول تناوبی، ساختارها و واکنش‌ها را به طور کامل یاد بگیرید تا دید شما به این درس تغییر کند.")
        cat1_feedback.append(
            "<strong>برنامه عملیاتی (تمرین مسئله‌محور):</strong> از آنجایی که در بخش‌های حفظی قوی هستید، پس از یادگیری مفاهیم، تمام تمرکز خود را روی تست‌های **محاسباتی، مسئله‌محور و مفهومی** شیمی، به خصوص در مبحث کلیدی استوکیومتری، قرار دهید تا این ضعف به نقطه قوت تبدیل شود.")

    if p.get('شیمی', 0) > 90 and p.get('زیست', 100) < 50:
        cat1_feedback.append(
            "<strong>تشخیص دقیق وضعیت شیمی-زیست:</strong> شما دارای ذهن تحلیلی و ساختاری بسیار خوبی هستید که در شیمی به شما کمک کرده، اما احتمالاً **زیست را به روش اشتباهی مطالعه می‌کنید**. بزرگترین خطای شما این است که زیست را یک درس صرفاً حفظی می‌دانید، در حالی که بخش عمده آن مفهومی است.")
        cat1_feedback.append(
            "<strong>راهکار استراتژیک (تغییر کامل روش مطالعه زیست):</strong> شما باید شیوه مطالعه خود را کاملاً متحول کنید. به جای حفظ کردن طوطی‌وار، به دنبال **درک شبکه‌ای و مقایسه‌ای** باشید. یعنی هنگام مطالعه یک فصل، آن را به مفاهیم فصول دیگر و حتی کتاب‌های سال‌های قبل و بعد ارتباط دهید.")
        cat1_feedback.append(
            "<strong>برنامه عملیاتی (یادگیری ترکیبی):</strong> از ابزارهایی مانند **نمودارهای ترکیبی** و خلاصه‌نویسی‌های مقایسه‌ای برای ارتباط دادن فصل‌ها به یکدیگر استفاده کنید. پس از رسیدن به درک مفهومی و شبکه‌ای، می‌توانید وارد مرحله تست‌زنی شوید تا این نوع یادگیری در ذهن شما تثبیت شود.")

    if cat1_feedback:
        feedback["تحلیل پیشرفته زوج درس‌ها"] = cat1_feedback

    cat2_feedback = []
    others_strong = lambda s: all(perc >= 70 for name, perc in p.items() if name != s)
    if p.get('فیزیک', 100) < 40 and others_strong('فیزیک'):
        cat2_feedback.append(
            "<strong>تشخیص ضعف اصلی در فیزیک:</strong> با وجود تسلط خوب شما در دروس محاسباتی و تحلیلی دیگر مانند ریاضی و شیمی، ضعف عمیق شما در فیزیک یک مشکل جدی و یک هشدار است. این وضعیت نشان می‌دهد مشکل احتمالاً ناشی از **درک پایه‌ای ضعیف یا روش مطالعه نادرست** در این درس خاص است.")
        cat2_feedback.append(
            "<strong>راهکار (ریشه‌یابی و ترمیم):</strong> ابتدا باید ریشه مشکل را به دقت پیدا کنید. آیا تمام مفاهیم پایه‌ای فیزیک را به خوبی درک کرده‌اید؟ اگر نه، با استفاده از منابعی مانند فیلم آموزشی، آن‌ها را از ابتدا و با حوصله یاد بگیرید. اگر مفاهیم را بلدید، پس مشکل از کمبود تمرین است و باید حجم تست‌زنی خود را افزایش دهید.")

    elif p.get('ریاضی', 100) < 40 and others_strong('ریاضی'):
        cat2_feedback.append(
            "<strong>تشخیص ضعف اصلی در ریاضی:</strong> از آنجایی که شما دروسی مثل فیزیک و شیمی که خودشان محاسبات دارند را خوب زده‌اید، ضعف شما در ریاضی احتمالاً یک مشکل بنیادی در محاسبات نیست، بلکه بیشتر به **کمبود تمرین هدفمند و آشنایی با تیپ سوالات** مربوط می‌شود.")
        cat2_feedback.append(
            "<strong>راهکار (افزایش حجم و سرعت تمرین):</strong> ابتدا مطمئن شوید روی تمام دروس پایه‌ای ریاضی تسلط کامل دارید. سپس، حجم تست‌زنی خود را به شدت افزایش دهید. به خصوص روی تست‌هایی کار کنید که به **سرعت عمل بالا** نیاز دارند. به یاد داشته باشید که درسی مانند ریاضی فقط با تمرین بسیار زیاد و آشنایی با انواع بی‌شمار سوالات به تسلط کامل می‌رسد.")

    elif p.get('زیست', 100) < 40 and others_strong('زیست'):
        cat2_feedback.append(
            "<strong>تشخیص ضعف اصلی در زیست:</strong> با وجود موفقیت در دروس دیگر، ضعف شما در زیست به عنوان یک درس رتبه‌ساز، یک نقطه ضعف بسیار مهم است. این مشکل به احتمال زیاد به **روش اشتباه مطالعه زیست** برمی‌گردد. شما باید از مطالعه صرفاً حفظی فاصله بگیرید.")
        cat2_feedback.append(
            "<strong>راهکار (مطالعه ترکیبی و مفهومی):</strong> شیوه مطالعه خود را به سمت **یادگیری مفهومی و ترکیبی** تغییر دهید. بین فصول مختلف کتاب و حتی سال‌های مختلف تحصیلی ارتباط برقرار کنید (درک شبکه‌ای) و برای نظم دادن به ذهن خود، اطلاعات را با خلاصه‌نویسی، ساختن جدول و درخت ذهنی مرتب کنید. این روش مطالعه، شما را به تسلط می‌رساند.")

    elif p.get('شیمی', 100) < 40 and others_strong('شیمی'):
        cat2_feedback.append(
            "<strong>تشخیص ضعف اصلی در شیمی:</strong> از آنجا که شما هم در دروس مفهومی (مانند زیست) و هم محاسباتی (مانند ریاضی) قوی هستید، ضعف شما در شیمی نیاز به بررسی دقیق‌تری دارد. این ضعف می‌تواند ناشی از گیج شدن بین مباحث مختلف این درس باشد.")
        cat2_feedback.append(
            "<strong>راهکار (تفکیک و ترمیم هدفمند):</strong> ابتدا مشخص کنید مشکل شما دقیقاً در کدام بخش شیمی است: مفهومی، محاسباتی یا حفظی؟ اگر در بخش مفهومی و محاسباتی ضعف دارید، احتمالاً پایه‌ی ضعیفی دارید و باید مفاهیم را از اول با ویدیو آموزشی یاد بگیرید. اگر مشکل در حفظیات است، باید با ابزارهایی مانند خلاصه‌نویسی و ساختن درخت ذهنی، بین مباحث مختلف ارتباط برقرار کنید تا مطالب برای شما یکپارچه شوند.")

    if cat2_feedback:
        feedback["تحلیل نقاط ضعف کلیدی"] = cat2_feedback

    cat3_4_feedback = []
    if all(perc < 30 for perc in all_perc):
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (بحرانی و نیازمند اقدام فوری):</strong> کسب نمره زیر ۳۰٪ در تمام دروس نشان می‌دهد که شما یا هنوز مطالعه جدی و مصمم را برای آزمون شروع نکرده‌اید، یا روش مطالعه شما از پایه و اساس اشتباه است و نیاز به بازنگری کامل دارد.")
        cat3_4_feedback.append(
            "<strong>برنامه عملیاتی (ایجاد عادت مطالعه):</strong> اگر هنوز شروع نکرده‌اید، بهترین کار این است که فوراً و بدون اتلاف وقت، با یک **برنامه سبک و از پایه‌ترین منابع** شروع کنید. هدف کوتاه‌مدت و اصلی شما در این مرحله نه تسلط، بلکه صرفاً «ایجاد عادت مطالعه روزانه» است. به تدریج و پس از شکل‌گیری عادت، برنامه را سنگین‌تر کنید.")

    elif all(30 <= perc < 50 for perc in all_perc):
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (در مسیر درست اما بازدهی پایین):</strong> شما در مسیر درستی قرار دارید و احتمالاً ساعت مطالعه خوبی هم دارید، اما هنوز به بازدهی مطلوب نرسیده‌اید. این وضعیت نشان می‌دهد که مباحث پایه‌ای را تا حدی بلدید اما این دانش هنوز خام است و تثبیت نشده.")
        cat3_4_feedback.append(
            "<strong>برنامه عملیاتی (تمرکز بر تست و تحلیل):</strong> در این مرحله، **تست‌زنی و حل سوال** بهترین و مؤثرترین روش برای پیشرفت شماست. به جای پراکندگی در مطالعه، هر هفته روی یک یا دو درس هدف‌گذاری کرده و با تست‌زنی موضوعی و ساده، سعی کنید درصد خود را حداقل به ۶۰٪ برسانید. صبور باشید، زیرا پیشرفت در این بازه کند است اما پس از مدتی جهش خواهید کرد.")

    elif sum(p < 30 for p in all_perc) >= 3 and sum(45 <= p < 55 for p in all_perc) == 1:
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (عدم تعادل شدید):</strong> شما یک نقطه قوت نسبی (درس با نمره حدود ۵۰) دارید که باید آن را با تست‌زنی تثبیت کنید، اما سایر دروس به طور کامل رها شده‌اند.")
        cat3_4_feedback.append(
            "<strong>راهکار (استفاده از نقطه قوت برای ایجاد انگیزه):</strong> برای دروس ضعیف، باید مطالعه را از پایه‌ترین منابع شروع کنید. از موفقیت نسبی در آن یک درس برای ایجاد انگیزه و بالا کشیدن بقیه دروس استفاده کنید. برنامه شما باید ترکیبی از تثبیت درس قوی‌تر و ساختن پایه برای دروس ضعیف‌تر باشد.")

    elif all(50 <= perc < 70 for perc in all_perc):
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (متوسط و پایدار اما غیررقابتی):</strong> نمرات شما در سطح متوسط قرار دارد؛ این یعنی پایه‌تان تا حد خوبی شکل گرفته ولی هنوز به سطح رقابتی و رتبه‌ساز نرسیده‌اید. دانش شما برای عبور از این مرحله کافی نیست و نیاز به عمق‌بخشی دارد.")
        cat3_4_feedback.append(
            "<strong>برنامه عملیاتی (ورود به سطح بالاتر):</strong> شما باید تمرکز خود را روی **تثبیت مطالب و ارتقای تدریجی مهارت تست‌زنی** بگذارید. مباحث پرتکرار و مهم آزمون را در اولویت قرار دهید و با استفاده از منابع سطح بالاتر و تست‌های زمان‌دار، تلاش کنید قدم به قدم وارد محدوده ۷۰٪ به بالا شوید.")

    elif all(70 <= perc < 90 for perc in all_perc):
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (عالی و آماده رقابت):</strong> شما به سطح بسیار خوبی از تسلط رسیده‌اید و حجم وسیعی از دروس را به خوبی درک کرده‌اید. در این مرحله، شما باید از فاز مطالعه مفهومی عبور کرده و وارد فاز کاملاً **رقابتی** شوید.")
        cat3_4_feedback.append(
            "<strong>برنامه عملیاتی (تمرکز بر کیفیت و سوالات دشوار):</strong> به یاد داشته باشید که هر ۱ درصد پیشرفت در این بازه بسیار دشوار و ارزشمند است. بهترین کار برای شما، تمرکز روی **تست‌های سخت‌تر، چالشی و نوآورانه** است تا از رقبای خود جلو بیفتید. اکنون کیفیت تحلیل یک تست سخت، بسیار مهم‌تر از کمیت تست‌های ساده است.")

    elif sum(70 <= p < 90 for p in all_perc) == 2 and sum(50 <= p < 70 for p in all_perc) == 2:
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (خوب با عدم تعادل جزئی):</strong> وضعیت کلی شما بسیار خوب است، زیرا درصدهایتان به هم نزدیک هستند و این نشان‌دهنده **تعادل** در مطالعه شماست. شما دو درس عالی و دو درس خوب دارید که این یک پلتفرم عالی برای رشد است.")
        cat3_4_feedback.append(
            "<strong>برنامه عملیاتی (حفظ تعادل و رشد همزمان):</strong> استراتژی شما باید دو بخش داشته باشد: اول، حفظ و ارتقای دروس قوی‌تر با زدن تست‌های چالشی‌تر. دوم، تقویت پایه دروس متوسط برای رساندن آن‌ها به سطح دروس قوی‌تر. هدف نهایی شما باید **حفظ این تعادل و رشد همزمان** همه دروس به بازه بالای ۹۰ درصد باشد.")

    elif sum(p >= 90 for p in all_perc) >= 1 and sum(50 <= p < 90 for p in all_perc) >= 3:
        cat3_4_feedback.append(
            "<strong>تشخیص وضعیت کلی (تک‌درس قوی و عدم تعادل):</strong> شما یک نقطه قوت بسیار بزرگ و یک درس رتبه‌ساز دارید که باید آن را حفظ کنید. اما موفقیت نهایی در کنکور با **«تعادل»** به دست می‌آید، نه فقط یک درسِ بالا.")
        cat3_4_feedback.append(
            "<strong>برنامه عملیاتی (انتقال اعتماد به نفس و ایجاد تعادل):</strong> احتمالاً شما زمان یا انرژی بسیار زیادی را صرف آن یک درس کرده‌اید. اکنون زمان آن است که ضمن حفظ آن درس با مرور و تست کمتر، بخش اصلی انرژی خود را به دروس دیگر اختصاص دهید. برای هر کدام از دروس دیگر یک نقشه جبرانی دقیق بچینید و با استفاده از **اعتماد به نفسی** که از موفقیت در درس قوی خود گرفته‌اید، آن‌ها را نیز گام به گام بالا بیاورید.")

    if cat3_4_feedback:
        feedback["تحلیل جامع سطح عملکرد"] = cat3_4_feedback

    # اگر هیچ قانونی اعمال نشد، یک پیام پیش‌فرض نمایش بده
    if not feedback:
        feedback["تحلیل جامع سطح عملکرد"] = [
            "وضعیت نمرات شما در هیچ‌کدام از الگوهای تحلیلی رایج قرار نگرفت. برای دریافت تحلیل دقیق‌تر، با یک مشاور صحبت کنید."]

    return feedback


def generate_report(request):
    test_results = request.session.get('test_results', {})
    if not test_results:
        messages.warning(request, "هیچ داده‌ای برای نمایش گزارش یافت نشد. لطفاً ابتدا اطلاعات آزمون را وارد کنید.")
        return redirect('dashboard')

    report_items = []
    for i, (subject, data) in enumerate(test_results.items()):
        report_items.append({
            'subject_name': subject,
            'subject_data': data,
            'feedback': generate_subject_feedback(subject, data),
            'chart_id': i
        })

    num_subjects = len(test_results)
    avg_percentage = sum(d['percentage'] for d in test_results.values()) / num_subjects if num_subjects > 0 else 0

    historical_feedback = []
    complementary_feedback = {}

    if request.user.is_authenticated:
        if not Exam.objects.filter(user=request.user).exists() and 'test_results' in request.session:
            historical_feedback.append(
                "این اولین آزمونی است که تحلیل می‌کنید. برای دریافت تحلیل روند، آن را ذخیره کنید.")
        else:
            historical_feedback = generate_historical_feedback(request.user, test_results)

        complementary_feedback = generate_complementary_feedback(test_results)
        exam_id = request.session.get('saved_exam_id')
        is_exam_saved = exam_id and Exam.objects.filter(id=exam_id, user=request.user).exists()
    else:
        is_exam_saved = False

    context = {
        'report_items': report_items,
        'today_jalali_date': jdatetime.datetime.now().strftime("%Y/%m/%d"),
        'avg_percentage': f"{avg_percentage:.1f}",
        'total_questions': sum(d['total'] for d in test_results.values()),
        'total_correct': sum(d['correct'] for d in test_results.values()),
        'total_wrong': sum(d['wrong'] for d in test_results.values()),
        'subjects_list': [item['subject_name'] for item in report_items],
        'percentages_list': [item['subject_data']['percentage'] for item in report_items],
        'historical_feedback': historical_feedback,
        'complementary_feedback': complementary_feedback,
        'is_exam_saved': is_exam_saved,
    }
    return render(request, 'analyzer/report.html', context)


@login_required
@csrf_exempt
def save_exam_to_db(request):
    if request.method == 'POST':
        if 'test_results' not in request.session or not request.session['test_results']:
            return JsonResponse({'status': 'error',
                                 'message': 'داده‌های آزمون در سشن یافت نشد. لطفاً به داشبورد بازگشته و دوباره شروع کنید.'},
                                status=400)

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

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر است.'}, status=400)


@login_required
def user_profile(request):
    user_exams = Exam.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'analyzer/profile.html', {'exams': user_exams})


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('dashboard')
    return render(request, 'analyzer/delete_account_confirm.html')


@login_required
def account_redirect(request):
    is_verified = request.user.emailaddress_set.filter(primary=True, verified=True).exists()
    if is_verified:
        return redirect('user_profile')
    else:
        messages.warning(request,
                         'حساب کاربری شما هنوز فعال نشده است. لطفاً ایمیل خود را برای لینک فعال‌سازی بررسی کنید.')
        logout(request)
        return redirect('account_login')


class CustomSignupView(SignupView):
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except socket.gaierror:
            messages.error(self.request,
                           "خطا در اتصال به سرور ایمیل. لطفاً از اتصال اینترنت خود اطمینان حاصل کرده و مجدداً تلاش کنید.")
            return self.form_invalid(form)


class CustomLoginView(LoginView):
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
    if request.method == 'POST':
        try:
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

            request.session['test_results'] = processed_results
            request.session.modified = True

            return JsonResponse(
                {'status': 'success', 'message': f'اطلاعات تمام دروس با موفقیت ثبت شد.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'خطا: {e}'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'متد درخواست نامعتبر است'}, status=400)