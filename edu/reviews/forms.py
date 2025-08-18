from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'placeholder': 'نظر خود را اینجا بنویسید...',
            }),
            'rating': forms.HiddenInput()  # ما رندر ستاره‌ها را دستی انجام می‌دهیم
        }
