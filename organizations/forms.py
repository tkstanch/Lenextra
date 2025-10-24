from django import forms
from django.utils import timezone
from .models import (
    University,
    College,
    StudentProfile,
    TaskSubmission,
    OrganizationStudentTracking,
)

class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ["name", "city", "country", "website", "logo", "slug", "is_active"]


class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ["name", "city", "country", "website", "logo", "slug", "is_active"]


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "university", "college", "school", "grade_level",
            "date_of_birth", "bio", "gpa", "avatar", "allow_tracking",
        ]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}


class TaskApplyForm(forms.Form):
    motivation = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Why are you a good fit?"}))


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ["url", "content", "attachment"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }


class OrganizationStudentTrackingForm(forms.ModelForm):
    class Meta:
        model = OrganizationStudentTracking
        fields = [
            "business",
            "student",
            "assigned_staff",
            "stage",
            "contact_method",
            "last_contacted",
            "next_follow_up",
            "notes",
            "is_active",
        ]
        widgets = {
            "last_contacted": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "next_follow_up": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }