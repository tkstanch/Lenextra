from django import forms
from django.utils import timezone
from .models import StudentProgress, ParentProfile


class StudentProgressForm(forms.ModelForm):
    class Meta:
        model = StudentProgress
        fields = (
            "student",
            "date",
            "completed_lessons",
            "time_spent_minutes",
            "average_score",
            "progress_percent",
            "notes",
        )
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "completed_lessons": forms.NumberInput(attrs={"min": 0}),
            "time_spent_minutes": forms.NumberInput(attrs={"min": 0}),
            "average_score": forms.NumberInput(attrs={"step": "0.01", "min": 0}),
            "progress_percent": forms.NumberInput(attrs={"min": 0, "max": 100}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, parent: ParentProfile | None = None, **kwargs):
        self.parent_profile = parent
        super().__init__(*args, **kwargs)
        if self.parent_profile:
            self.fields["student"].queryset = self.parent_profile.students.select_related("user")
        if not self.initial.get("date"):
            self.initial["date"] = timezone.localdate()

    def clean_student(self):
        student = self.cleaned_data.get("student")
        if self.parent_profile and student and not self.parent_profile.students.filter(pk=student.pk).exists():
            raise forms.ValidationError("Selected student is not linked to your profile.")
        return student

    def clean(self):
        cleaned = super().clean()
        parent = self.parent_profile or getattr(self.instance, "parent", None)
        student = cleaned.get("student")
        date = cleaned.get("date")
        if parent and student and date:
            qs = StudentProgress.objects.filter(parent=parent, student=student, date=date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("An entry already exists for this student and date.")
        return cleaned