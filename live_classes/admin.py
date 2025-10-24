from django.contrib import admin
from .models import LiveClassRequest, LiveClassSession, TutorAvailability

@admin.register(LiveClassRequest)
class LiveClassRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "requested_by", "status", "created_at")
    list_filter = ("status", "created_at", "course")
    search_fields = ("id", "requested_by__username", "course__title", "topic")

@admin.register(LiveClassSession)
class LiveClassSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "start_at", "duration_minutes", "provider")
    list_filter = ("provider", "start_at", "course")
    search_fields = ("id", "course__title", "meeting_code", "meeting_url")

@admin.register(TutorAvailability)
class TutorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("id", "tutor", "weekday", "start_time", "end_time", "active")
    list_filter = ("weekday", "active")
    search_fields = ("tutor__username", "tutor__email")
