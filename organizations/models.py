from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class StudentProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")

    # New links to higher-ed
    university = models.ForeignKey("organizations.University", on_delete=models.SET_NULL, blank=True, null=True, related_name="students")
    college = models.ForeignKey("organizations.College", on_delete=models.SET_NULL, blank=True, null=True, related_name="students")

    # Legacy/optional free-text
    school = models.CharField(max_length=255, blank=True, null=True)
    grade_level = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(13)]
    )
    allow_tracking = models.BooleanField(default=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    gpa = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(4)]
    )
    avatar = models.ImageField(upload_to="students/avatars/", blank=True, null=True)
    enrollment_year = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()


class IndustryTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)  # NEW

    class Meta:
        ordering = ("name",)  # avoid ordering by slug
        verbose_name = "Industry tag"
        verbose_name_plural = "Industry tags"

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug and getattr(self, "name", None):
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SkillTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)  # NEW

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("name",)  # avoid slug ordering until column exists
        verbose_name = "Skill tag"
        verbose_name_plural = "Skill tags"

    def __str__(self):
        return self.name


class Business(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    # fields expected by your forms
    verified = models.BooleanField(default=False)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)

    # note: forms expect 'industry' (singular). Keep this name.
    industry = models.ManyToManyField(IndustryTag, related_name="businesses", blank=True)
    # optional skills relation (safe to keep)
    skills = models.ManyToManyField(SkillTag, related_name="businesses", blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class School(TimeStampedModel):  # changed from models.Model
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)
    ranking = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not getattr(self, "slug", None):
            base = slugify(getattr(self, "name", "") or "") or "school"
            max_len = self._meta.get_field("slug").max_length
            slug = base[:max_len]
            i = 1
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                suffix = f"-{i}"
                slug = f"{base[: max_len - len(suffix) ]}{suffix}"
            self.slug = slug
        return super().save(*args, **kwargs)


class Partnership(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="partnerships")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="partnerships")
    active = models.BooleanField(default=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("ended", "Ended"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # NEW: timestamps used by dashboard/admin
    created_at = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ("business", "school")


class BusinessStudentTracking(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="tracked_students")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="tracked_by_businesses")

    tracking_reason = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    stage = models.CharField(max_length=50, blank=True, null=True)
    last_contacted = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Optional: add timestamps for consistency
    created_at = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ("business", "student")


class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base = slugify(self.name) or "university"
            candidate = base[:255]
            i = 1
            while University.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                i += 1
                suffix = f"-{i}"
                candidate = f"{base[:255 - len(suffix)]}{suffix}"
            self.slug = candidate
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class College(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base = slugify(self.name) or "college"
            candidate = base[:255]
            i = 1
            while College.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                i += 1
                suffix = f"-{i}"
                candidate = f"{base[:255 - len(suffix)]}{suffix}"
            self.slug = candidate
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Organization tasking system
TASK_STATUS = [
    ("draft", "Draft"),
    ("open", "Open"),
    ("closed", "Closed"),
    ("archived", "Archived"),
]

APPLICATION_STATUS = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("withdrawn", "Withdrawn"),
    ("completed", "Completed"),
]

SUBMISSION_STATUS = [
    ("submitted", "Submitted"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]

class OrganizationTask(TimeStampedModel):
    business = models.ForeignKey("organizations.Business", on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    difficulty = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    points = models.PositiveIntegerField(default=10)
    deadline = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default="open", db_index=True)
    required_skills = models.ManyToManyField("organizations.SkillTag", blank=True, related_name="tasks")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "task"
            # ensure uniqueness across business
            candidate = base
            i = 1
            while OrganizationTask.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                i += 1
                candidate = f"{base}-{i}"
            self.slug = candidate[:240]
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.business.name}: {self.title}"

class TaskApplication(TimeStampedModel):
    task = models.ForeignKey(OrganizationTask, on_delete=models.CASCADE, related_name="applications")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="task_applications")
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default="pending", db_index=True)
    motivation = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_task_applications")
    due_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("task", "student")

    def __str__(self):
        return f"{self.student} -> {self.task} [{self.status}]"

class TaskSubmission(TimeStampedModel):
    application = models.OneToOneField(TaskApplication, on_delete=models.CASCADE, related_name="submission")
    url = models.URLField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to="org_tasks/submissions/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default="submitted", db_index=True)
    feedback = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_task_submissions")
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Submission for {self.application}"

class StudentAchievement(TimeStampedModel):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="achievements")
    business = models.ForeignKey("organizations.Business", on_delete=models.CASCADE, related_name="issued_achievements")
    task = models.ForeignKey(OrganizationTask, on_delete=models.SET_NULL, null=True, blank=True, related_name="achievements")
    title = models.CharField(max_length=255)
    points = models.PositiveIntegerField(default=0)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.title} ({self.points} pts)"


TRACKING_STAGE = [
    ("lead", "Lead"),
    ("contacted", "Contacted"),
    ("interview", "Interview/Meeting"),
    ("engaged", "Engaged/Active"),
    ("completed", "Completed"),
    ("dropped", "Dropped"),
]

CONTACT_METHOD = [
    ("email", "Email"),
    ("phone", "Phone"),
    ("meeting", "Meeting"),
    ("other", "Other"),
]

class OrganizationStudentTracking(models.Model):
    business = models.ForeignKey("organizations.Business", on_delete=models.CASCADE, related_name="student_trackings")
    student = models.ForeignKey("organizations.StudentProfile", on_delete=models.CASCADE, related_name="org_trackings")
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_trackings")
    stage = models.CharField(max_length=20, choices=TRACKING_STAGE, default="lead", db_index=True)
    contact_method = models.CharField(max_length=20, choices=CONTACT_METHOD, blank=True, null=True)
    last_contacted = models.DateTimeField(blank=True, null=True)
    next_follow_up = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("business", "student")
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.business} -> {self.student} [{self.stage}]"