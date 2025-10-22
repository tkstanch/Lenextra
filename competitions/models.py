from django.db import models, transaction
from django.db.models import F, Index, Q
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.conf import settings

# Create your models here.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class Competition(TimeStampedModel):
    COMP_TYPE_CHOICES = [
        ("local", "Local"),
        ("world_cup", "World Cup"),
    ]
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    comp_type = models.CharField(max_length=20, choices=COMP_TYPE_CHOICES)
    description = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    # Optional categorization (align with organizations)
    discipline = models.ForeignKey(
        "organizations.SkillTag", on_delete=models.SET_NULL, null=True, blank=True, related_name="competitions"
    )

    # Participation limits (0 = unlimited)
    max_schools = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    max_students = models.PositiveIntegerField(default=0, help_text="0 means unlimited")

    # Relations via through models
    schools = models.ManyToManyField(
        "organizations.School", through="SchoolCompetitionEntry", related_name="competitions", blank=True
    )
    students = models.ManyToManyField(
        "organizations.StudentProfile", through="StudentCompetitionEntry", related_name="competitions", blank=True
    )

    class Meta:
        ordering = ["-start_date", "name"]
        indexes = [
            Index(fields=["slug"]),
            Index(fields=["comp_type"]),
            Index(fields=["start_date", "end_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(end_date__gte=models.F("start_date")),
                name="competition_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_comp_type_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("competitions:competition_detail", args=[self.slug])

    @property
    def status(self) -> str:
        today = timezone.localdate()
        if self.start_date and today < self.start_date:
            return "upcoming"
        if self.end_date and today > self.end_date:
            return "finished"
        return "ongoing"

    def can_join_schools(self) -> bool:
        return self.max_schools == 0 or self.entries.count() < self.max_schools

    def can_join_students(self) -> bool:
        return self.max_students == 0 or self.student_entries.count() < self.max_students

    def join_school(self, school: "organizations.School") -> "SchoolCompetitionEntry":
        if not self.is_active:
            raise ValidationError("Competition is not active.")
        if self.status == "finished":
            raise ValidationError("Competition has finished.")
        if not self.can_join_schools():
            raise ValidationError("School capacity for this competition is full.")
        entry, created = SchoolCompetitionEntry.objects.get_or_create(
            competition=self, school=school, defaults={"score": 0}
        )
        if not created and entry.disqualified:
            raise ValidationError("This school was disqualified and cannot rejoin.")
        return entry

    def join_student(self, student: "organizations.StudentProfile") -> "StudentCompetitionEntry":
        if not self.is_active:
            raise ValidationError("Competition is not active.")
        if self.status == "finished":
            raise ValidationError("Competition has finished.")
        if not self.can_join_students():
            raise ValidationError("Student capacity for this competition is full.")
        entry, created = StudentCompetitionEntry.objects.get_or_create(
            competition=self, student=student, defaults={"score": 0}
        )
        if not created and entry.disqualified:
            raise ValidationError("This student was disqualified and cannot rejoin.")
        return entry

    def leaderboard_schools(self):
        return (
            self.entries.select_related("school")
            .only("id", "competition_id", "school_id", "score", "rank", "disqualified")
            .order_by("-score", "created_at")
        )

    def leaderboard_students(self):
        return (
            self.student_entries.select_related("student__user", "student__school")
            .only("id", "competition_id", "student_id", "score", "rank", "disqualified")
            .order_by("-score", "created_at")
        )

    def record_points_for_school(self, school, points: int, reason: str = "", category: str = "manual", by=None):
        entry = self.join_school(school)
        return entry.add_points(points, reason=reason, category=category, by=by)

    def record_points_for_student(self, student, points: int, reason: str = "", category: str = "manual", by=None):
        entry = self.join_student(student)
        return entry.add_points(points, reason=reason, category=category, by=by)


class SchoolCompetitionEntry(TimeStampedModel):
    school = models.ForeignKey(
        "organizations.School", on_delete=models.CASCADE, related_name="competition_entries"
    )
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="entries")
    score = models.IntegerField(default=0, db_index=True)
    rank = models.PositiveIntegerField(default=0, help_text="Optional cached rank")
    disqualified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("school", "competition")
        ordering = ["-score", "created_at"]
        indexes = [
            Index(fields=["competition", "-score"]),
            Index(fields=["school", "competition"]),
        ]

    def __str__(self):
        return f"{self.school} in {self.competition} — {self.score} pts"

    @transaction.atomic
    def add_points(self, points: int, reason: str = "", category: str = "manual", by=None):
        # Atomic increment and audit trail
        type(self).objects.filter(pk=self.pk).update(score=F("score") + points)
        self.refresh_from_db(fields=["score"])
        CompetitionScoreEvent.objects.create(
            competition=self.competition,
            school=self.school,
            points=points,
            category=category,
            reason=reason or "",
            created_by=by if isinstance(by, settings.AUTH_USER_MODEL.__class__) else None,  # may be None
        )
        return self.score

    def disqualify(self, reason: str = "", by=None):
        self.disqualified = True
        self.save(update_fields=["disqualified", "updated_at"])
        CompetitionDisqualification.objects.create(
            competition=self.competition,
            school=self.school,
            reason=reason or "",
            created_by=by if isinstance(by, settings.AUTH_USER_MODEL.__class__) else None,
        )


class StudentCompetitionEntry(TimeStampedModel):
    student = models.ForeignKey(
        "organizations.StudentProfile", on_delete=models.CASCADE, related_name="competition_entries"
    )
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="student_entries")
    score = models.IntegerField(default=0, db_index=True)
    rank = models.PositiveIntegerField(default=0, help_text="Optional cached rank")
    disqualified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("student", "competition")
        ordering = ["-score", "created_at"]
        indexes = [
            Index(fields=["competition", "-score"]),
            Index(fields=["student", "competition"]),
        ]

    def __str__(self):
        return f"{self.student} in {self.competition} — {self.score} pts"

    @transaction.atomic
    def add_points(self, points: int, reason: str = "", category: str = "manual", by=None):
        type(self).objects.filter(pk=self.pk).update(score=F("score") + points)
        self.refresh_from_db(fields=["score"])
        CompetitionScoreEvent.objects.create(
            competition=self.competition,
            student=self.student,
            points=points,
            category=category,
            reason=reason or "",
            created_by=by if isinstance(by, settings.AUTH_USER_MODEL.__class__) else None,
        )
        return self.score

    def disqualify(self, reason: str = "", by=None):
        self.disqualified = True
        self.save(update_fields=["disqualified", "updated_at"])
        CompetitionDisqualification.objects.create(
            competition=self.competition,
            student=self.student,
            reason=reason or "",
            created_by=by if isinstance(by, settings.AUTH_USER_MODEL.__class__) else None,
        )


class CompetitionScoreEvent(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("manual", "Manual"),
        ("activity", "Activity"),
        ("bonus", "Bonus"),
        ("penalty", "Penalty"),
    ]
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="score_events")
    # One of these will be set
    school = models.ForeignKey(
        "organizations.School", on_delete=models.CASCADE, null=True, blank=True, related_name="competition_scores"
    )
    student = models.ForeignKey(
        "organizations.StudentProfile", on_delete=models.CASCADE, null=True, blank=True, related_name="competition_scores"
    )

    points = models.IntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="manual")
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="competition_events"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["competition", "-created_at"]),
            Index(fields=["school"]),
            Index(fields=["student"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(school__isnull=False, student__isnull=True)
                | Q(school__isnull=True, student__isnull=False),
                name="score_event_one_target",
            )
        ]

    def __str__(self):
        target = self.school or self.student
        return f"{self.points:+} pts to {target} @ {self.competition}"


class CompetitionDisqualification(TimeStampedModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="disqualifications")
    school = models.ForeignKey(
        "organizations.School", on_delete=models.CASCADE, null=True, blank=True, related_name="disqualifications"
    )
    student = models.ForeignKey(
        "organizations.StudentProfile", on_delete=models.CASCADE, null=True, blank=True, related_name="disqualifications"
    )
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="competition_disq"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(school__isnull=False, student__isnull=True)
                | Q(school__isnull=True, student__isnull=False),
                name="disq_one_target",
            )
        ]

    def __str__(self):
        target = self.school or self.student
        return f"DQ: {target} from {self.competition}"
