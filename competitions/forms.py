from django import forms
from django.utils import timezone
from django.db.models import Q
from django.db import models

from .models import (
    Competition,
    SchoolCompetitionEntry,
    StudentCompetitionEntry,
    CompetitionScoreEvent,
    CompetitionDisqualification,
)

_date_widget = forms.DateInput(attrs={"type": "date"})


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = [
            "name",
            "slug",
            "comp_type",
            "description",
            "start_date",
            "end_date",
            "discipline",
            "max_schools",
            "max_students",
            "is_active",
        ]
        widgets = {
            "start_date": _date_widget,
            "end_date": _date_widget,
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "slug": "Leave blank to auto-generate from name.",
            "max_schools": "0 means unlimited.",
            "max_students": "0 means unlimited.",
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after start date.")
        return cleaned


class JoinCompetitionForm(forms.ModelForm):
    class Meta:
        model = SchoolCompetitionEntry
        fields = ['school']


class SchoolJoinForm(forms.ModelForm):
    """
    Join a school to a competition.
    Pass competition=<Competition> to __init__.
    Filters out already-joined schools and enforces capacity.
    """
    school = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = SchoolCompetitionEntry
        fields = ["school"]

    def __init__(self, *args, competition: Competition | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        qs = self._eligible_schools_qs()
        self.fields["school"].queryset = qs

    def _eligible_schools_qs(self):
        from organizations.models import School  # local import to avoid circulars
        qs = School.objects.filter(is_active=True)
        if self.competition:
            joined_ids = SchoolCompetitionEntry.objects.filter(
                competition=self.competition
            ).values_list("school_id", flat=True)
            qs = qs.exclude(id__in=joined_ids)
        return qs

    def clean(self):
        cleaned = super().clean()
        comp = self.competition
        school = cleaned.get("school")
        if not comp:
            raise forms.ValidationError("Competition context is required.")
        if comp.status == "finished":
            raise forms.ValidationError("Cannot join a finished competition.")
        # Capacity check
        if comp.max_schools and comp.entries.count() >= comp.max_schools:
            raise forms.ValidationError("School capacity for this competition is full.")
        # Duplicate check
        if school and SchoolCompetitionEntry.objects.filter(competition=comp, school=school).exists():
            self.add_error("school", "This school is already participating.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.competition = self.competition
        if commit:
            obj.save()
        return obj


class StudentJoinForm(forms.ModelForm):
    """
    Join a student to a competition.
    Pass competition=<Competition> to __init__.
    Filters out already-joined students and enforces capacity.
    If competition.discipline is set, prefers students with that skill (not enforced).
    """
    student = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = StudentCompetitionEntry
        fields = ["student"]

    def __init__(self, *args, competition: Competition | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        self.fields["student"].queryset = self._eligible_students_qs()

    def _eligible_students_qs(self):
        from organizations.models import StudentProfile  # local import to avoid circulars
        qs = StudentProfile.objects.filter(is_active=True)
        if self.competition:
            joined_ids = StudentCompetitionEntry.objects.filter(
                competition=self.competition
            ).values_list("student_id", flat=True)
            qs = qs.exclude(id__in=joined_ids)
            # Optional: nudge by discipline (no hard filter to avoid empty lists)
            if self.competition.discipline_id:
                qs = qs.order_by(
                    # bring students with the discipline skill to the top
                    models.Case(
                        models.When(skills__id=self.competition.discipline_id, then=0),
                        default=1,
                        output_field=models.IntegerField(),
                    ),
                    "user__username",
                ).distinct()
        return qs.select_related("user", "school").prefetch_related("skills")

    def clean(self):
        cleaned = super().clean()
        comp = self.competition
        student = cleaned.get("student")
        if not comp:
            raise forms.ValidationError("Competition context is required.")
        if comp.status == "finished":
            raise forms.ValidationError("Cannot join a finished competition.")
        if comp.max_students and comp.student_entries.count() >= comp.max_students:
            raise forms.ValidationError("Student capacity for this competition is full.")
        if student and StudentCompetitionEntry.objects.filter(competition=comp, student=student).exists():
            self.add_error("student", "This student is already participating.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.competition = self.competition
        if commit:
            obj.save()
        return obj


class ScorePointsForm(forms.Form):
    """
    Add points to either a school or student entry (exactly one target).
    Pass competition=<Competition> to __init__.
    """
    points = forms.IntegerField(help_text="Positive to add points, negative to deduct.")
    category = forms.ChoiceField(choices=CompetitionScoreEvent.CATEGORY_CHOICES, initial="manual")
    reason = forms.CharField(max_length=255, required=False)
    school_entry = forms.ModelChoiceField(queryset=SchoolCompetitionEntry.objects.none(), required=False)
    student_entry = forms.ModelChoiceField(queryset=StudentCompetitionEntry.objects.none(), required=False)

    def __init__(self, *args, competition: Competition | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        if competition:
            self.fields["school_entry"].queryset = SchoolCompetitionEntry.objects.filter(
                competition=competition, disqualified=False
            ).select_related("school")
            self.fields["student_entry"].queryset = StudentCompetitionEntry.objects.filter(
                competition=competition, disqualified=False
            ).select_related("student__user", "student__school")

    def clean(self):
        cleaned = super().clean()
        s_entry = cleaned.get("school_entry")
        st_entry = cleaned.get("student_entry")
        if bool(s_entry) == bool(st_entry):
            raise forms.ValidationError("Select either a school OR a student.")
        # Ensure entries belong to the same competition context
        if s_entry and self.competition and s_entry.competition_id != self.competition.id:
            self.add_error("school_entry", "Invalid selection.")
        if st_entry and self.competition and st_entry.competition_id != self.competition.id:
            self.add_error("student_entry", "Invalid selection.")
        return cleaned

    def save(self, user=None):
        points = self.cleaned_data["points"]
        category = self.cleaned_data["category"]
        reason = self.cleaned_data.get("reason") or ""
        s_entry = self.cleaned_data.get("school_entry")
        st_entry = self.cleaned_data.get("student_entry")
        if s_entry:
            s_entry.add_points(points, reason=reason, category=category, by=user)
            return s_entry
        else:
            st_entry.add_points(points, reason=reason, category=category, by=user)
            return st_entry


class DisqualifyForm(forms.Form):
    """
    Disqualify either a school or a student entry (exactly one target).
    Pass competition=<Competition> to __init__.
    """
    reason = forms.CharField(max_length=255, required=False)
    school_entry = forms.ModelChoiceField(queryset=SchoolCompetitionEntry.objects.none(), required=False)
    student_entry = forms.ModelChoiceField(queryset=StudentCompetitionEntry.objects.none(), required=False)

    def __init__(self, *args, competition: Competition | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        if competition:
            self.fields["school_entry"].queryset = SchoolCompetitionEntry.objects.filter(
                competition=competition, disqualified=False
            ).select_related("school")
            self.fields["student_entry"].queryset = StudentCompetitionEntry.objects.filter(
                competition=competition, disqualified=False
            ).select_related("student__user", "student__school")

    def clean(self):
        cleaned = super().clean()
        s_entry = cleaned.get("school_entry")
        st_entry = cleaned.get("student_entry")
        if bool(s_entry) == bool(st_entry):
            raise forms.ValidationError("Select either a school OR a student.")
        return cleaned

    def save(self, user=None):
        reason = self.cleaned_data.get("reason") or ""
        s_entry = self.cleaned_data.get("school_entry")
        st_entry = self.cleaned_data.get("student_entry")
        if s_entry:
            s_entry.disqualify(reason=reason, by=user)
            return s_entry
        else:
            st_entry.disqualify(reason=reason, by=user)
            return st_entry


class LeaderboardFilterForm(forms.Form):
    """
    Optional filter form for leaderboard pages.
    """
    q = forms.CharField(required=False, label="Search")
    min_points = forms.IntegerField(required=False)
    max_points = forms.IntegerField(required=False)
    only_active = forms.BooleanField(required=False, initial=True, help_text="Hide disqualified entries")

    def apply_to_school_qs(self, qs):
        if self.is_valid():
            q = (self.cleaned_data.get("q") or "").strip()
            if q:
                qs = qs.filter(
                    Q(school__name__icontains=q)
                    | Q(competition__name__icontains=q)
                )
            if self.cleaned_data.get("min_points") is not None:
                qs = qs.filter(score__gte=self.cleaned_data["min_points"])
            if self.cleaned_data.get("max_points") is not None:
                qs = qs.filter(score__lte=self.cleaned_data["max_points"])
            if self.cleaned_data.get("only_active"):
                qs = qs.filter(disqualified=False)
        return qs

    def apply_to_student_qs(self, qs):
        if self.is_valid():
            q = (self.cleaned_data.get("q") or "").strip()
            if q:
                qs = qs.filter(
                    Q(student__user__username__icontains=q)
                    | Q(student__user__first_name__icontains=q)
                    | Q(student__user__last_name__icontains=q)
                    | Q(competition__name__icontains=q)
                )
            if self.cleaned_data.get("min_points") is not None:
                qs = qs.filter(score__gte=self.cleaned_data["min_points"])
            if self.cleaned_data.get("max_points") is not None:
                qs = qs.filter(score__lte=self.cleaned_data["max_points"])
            if self.cleaned_data.get("only_active"):
                qs = qs.filter(disqualified=False)
        return qs