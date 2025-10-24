from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

PROVIDERS = [
    ("jitsi", "Jitsi"),
    ("zoom", "Zoom"),
    ("twilio", "Twilio"),
]

REQUEST_STATUS = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("scheduled", "Scheduled"),
]

def generate_room_slug(prefix: str = "lenextra") -> str:
    return f"{prefix}-{get_random_string(8)}"

class LiveClassRequest(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="live_class_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_class_requests")
    topic = models.CharField(max_length=255, blank=True)
    preferred_times = models.TextField(blank=True, help_text="Student-proposed times or notes")
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default="pending", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request #{self.id} {self.course} by {self.requested_by} [{self.status}]"

class LiveClassSession(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="live_class_sessions")
    request = models.OneToOneField(LiveClassRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="session")
    scheduled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="scheduled_live_classes")
    assigned_tutor = models.ForeignKey(  # NEW
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_live_classes"
    )
    start_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    provider = models.CharField(max_length=20, choices=PROVIDERS, default="jitsi", db_index=True)
    meeting_url = models.URLField(blank=True, null=True)
    meeting_code = models.CharField(max_length=255, blank=True, null=True)
    invited_students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="live_class_sessions")
    ended_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Live {self.provider} on {self.start_at} for {self.course}"

    @staticmethod
    def build_meeting_url(provider: str = "jitsi", room_slug: str | None = None) -> tuple[str, str | None]:
        # Delegates to provider services; falls back to Jitsi room URL.
        try:
            if provider == "zoom":
                from .services.providers.zoom import create_meeting
                return create_meeting()
            if provider == "twilio":
                from .services.providers.twilio import create_meeting
                return create_meeting()
        except Exception:
            pass
        room = room_slug or generate_room_slug()
        return f"https://meet.jit.si/{room}", room

class TutorAvailability(models.Model):
    # Weekly availability windows for tutors/staff
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_availability")
    weekday = models.IntegerField(choices=[(i, d) for i, d in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])], db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Tutor availability"
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gt=models.F("start_time")), name="live_avail_end_after_start"),
        ]

    def __str__(self):
        return f"{self.tutor} {self.weekday} {self.start_time}-{self.end_time}"
