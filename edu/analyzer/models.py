# analyzer/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

class Exam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams')
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