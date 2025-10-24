from django.contrib import admin
from .models import ParentProfile, StudentProgress


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "city", "country", "is_active", "created_at")
    list_filter = ("is_active", "city", "country")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "city",
        "country",
        "phone",
    )
    raw_id_fields = ("user", "students")
    filter_horizontal = ("students",)
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "parent",
        "student",
        "date",
        "completed_lessons",
        "time_spent_minutes",
        "average_score",
        "progress_percent",
        "updated_at",
    )
    list_filter = ("date", "parent__is_active")
    search_fields = (
        "parent__user__username",
        "parent__user__email",
        "parent__user__first_name",
        "parent__user__last_name",
        "student__user__username",
        "student__user__first_name",
        "student__user__last_name",
        "notes",
    )
    raw_id_fields = ("parent", "student")
    list_select_related = ("parent", "student")
    date_hierarchy = "date"
    ordering = ("-date", "-updated_at")
    list_per_page = 50