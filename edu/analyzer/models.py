# analyzer/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings




class Exam(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exams')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_average_percentage(self):
        return self.subjects.aggregate(avg_percentage=Avg('percentage'))['avg_percentage'] or 0

    def __str__(self):
        return f"آزمون کاربر {self.user.username} در {self.created_at.strftime('%Y/%m/%d')}"

class SubjectResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=100)
    correct = models.IntegerField()
    wrong = models.IntegerField()
    blank = models.IntegerField()
    total = models.IntegerField()
    percentage = models.FloatField()
    study_hours = models.FloatField(default=0)
    practice = models.IntegerField(default=0)
    risk_management = models.FloatField(default=0)
    answering_efficiency = models.FloatField(default=0)
    study_productivity = models.FloatField(default=0)
    practice_effectiveness = models.FloatField(default=0)
    time_utilization = models.FloatField(default=0)

    def __str__(self):
        return f"{self.subject_name} - {self.percentage:.1f}%"

    username_validator = RegexValidator(
        r'^[a-zA-Z0-9\u0600-\u06FF\s]+$',
        'نام کاربری فقط می‌تواند شامل حروف، اعداد و فاصله باشد.'
    )



class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                r'^[a-zA-Z0-9\u0600-\u06FF\s]+$',
                'نام کاربری فقط می‌تواند شامل حروف، اعداد و فاصله باشد.'
            )
        ],
        verbose_name="نام کاربری"
    )

    first_name = models.CharField(max_length=150, blank=True, verbose_name="نام")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="نام خانوادگی")

    def __str__(self):
        return self.username
