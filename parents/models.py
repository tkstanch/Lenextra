from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ParentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
    )
    students = models.ManyToManyField(
        "organizations.StudentProfile",
        related_name="parents",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"ParentProfile({self.user})"


class StudentProgress(models.Model):
    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    student = models.ForeignKey(
        "organizations.StudentProfile",
        on_delete=models.CASCADE,
        related_name="daily_progress",
    )

    date = models.DateField()
    time_spent_minutes = models.PositiveIntegerField(default=0)
    completed_lessons = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    notes = models.TextField(blank=True, null=True)
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("-date", "-updated_at", "-id")
        unique_together = (("parent", "student", "date"),)

    def __str__(self) -> str:
        return f"{self.student} {self.date} ({self.progress_percent}%)"