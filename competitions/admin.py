from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
import csv

from .models import (
    Competition,
    SchoolCompetitionEntry,
    StudentCompetitionEntry,
    CompetitionScoreEvent,
    CompetitionDisqualification,
)


class BaseTimestampedAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("is_active",)
    date_hierarchy = "created_at"
    list_per_page = 50


class SchoolCompetitionEntryInline(admin.TabularInline):
    model = SchoolCompetitionEntry
    extra = 0
    show_change_link = True
    autocomplete_fields = ("school",)
    fields = ("school", "score", "rank", "disqualified", "is_active", "created_at")
    readonly_fields = ("created_at",)


class StudentCompetitionEntryInline(admin.TabularInline):
    model = StudentCompetitionEntry
    extra = 0
    show_change_link = True
    autocomplete_fields = ("student",)
    fields = ("student", "score", "rank", "disqualified", "is_active", "created_at")
    readonly_fields = ("created_at",)


@admin.action(description="Activate selected competitions")
def activate_competitions(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Deactivate selected competitions")
def deactivate_competitions(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description="Recalculate ranks for selected competitions")
def recalc_ranks(modeladmin, request, queryset):
    """
    Dense-rank by score (higher score -> rank 1). Ties share rank.
    """
    total_updated = 0
    for comp in queryset:
        # Schools
        entries = list(
            SchoolCompetitionEntry.objects.filter(competition=comp)
            .only("id", "score", "rank")
            .order_by("-score", "created_at")
        )
        rank = 0
        last_score = None
        for idx, e in enumerate(entries, start=1):
            if e.score != last_score:
                rank += 1
            last_score = e.score
            if e.rank != rank:
                e.rank = rank
        SchoolCompetitionEntry.objects.bulk_update(entries, ["rank"])
        total_updated += len(entries)

        # Students
        sentries = list(
            StudentCompetitionEntry.objects.filter(competition=comp)
            .only("id", "score", "rank")
            .order_by("-score", "created_at")
        )
        rank = 0
        last_score = None
        for idx, e in enumerate(sentries, start=1):
            if e.score != last_score:
                rank += 1
            last_score = e.score
            if e.rank != rank:
                e.rank = rank
        StudentCompetitionEntry.objects.bulk_update(sentries, ["rank"])
        total_updated += len(sentries)

    modeladmin.message_user(request, f"Ranks recalculated for {queryset.count()} competitions (entries updated: {total_updated}).")


@admin.action(description="Export school leaderboards (CSV)")
def export_school_leaderboard_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="school_leaderboards_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["competition", "school", "score", "rank", "disqualified"])
    for comp in queryset:
        for e in SchoolCompetitionEntry.objects.select_related("school").filter(competition=comp).order_by("-score", "created_at"):
            writer.writerow([comp.name, e.school.name, e.score, e.rank, "yes" if e.disqualified else "no"])
    return response


@admin.action(description="Export student leaderboards (CSV)")
def export_student_leaderboard_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="student_leaderboards_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["competition", "student", "school", "score", "rank", "disqualified"])
    for comp in queryset:
        qs = StudentCompetitionEntry.objects.select_related("student__user", "student__school").filter(competition=comp).order_by("-score", "created_at")
        for e in qs:
            student_name = e.student.user.get_full_name() or e.student.user.username
            school_name = e.student.school.name if e.student.school_id else "-"
            writer.writerow([comp.name, student_name, school_name, e.score, e.rank, "yes" if e.disqualified else "no"])
    return response


@admin.register(Competition)
class CompetitionAdmin(BaseTimestampedAdmin):
    list_display = (
        "name",
        "comp_type",
        "discipline",
        "start_date",
        "end_date",
        "status_display",
        "school_count",
        "student_count",
        "is_active",
        "created_at",
    )
    list_filter = ("comp_type", "discipline", "is_active", "start_date", "end_date")
    search_fields = ("name", "description", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (SchoolCompetitionEntryInline, StudentCompetitionEntryInline)
    actions = (
        activate_competitions,
        deactivate_competitions,
        recalc_ranks,
        export_school_leaderboard_csv,
        export_student_leaderboard_csv,
    )

    def status_display(self, obj):
        return obj.status
    status_display.short_description = "Status"

    def school_count(self, obj):
        return obj.entries.count()
    school_count.short_description = "Schools"

    def student_count(self, obj):
        return obj.student_entries.count()
    student_count.short_description = "Students"


@admin.action(description="Disqualify selected entries")
def disqualify_entries(modeladmin, request, queryset):
    queryset.update(disqualified=True)


@admin.action(description="Re-qualify selected entries")
def requalify_entries(modeladmin, request, queryset):
    queryset.update(disqualified=False)


@admin.action(description="Reset scores to 0")
def reset_scores(modeladmin, request, queryset):
    queryset.update(score=0, rank=0)


@admin.register(SchoolCompetitionEntry)
class SchoolCompetitionEntryAdmin(BaseTimestampedAdmin):
    list_display = ("school", "competition", "score", "rank", "disqualified", "is_active", "created_at")
    list_filter = ("competition", "disqualified", "is_active")
    search_fields = ("school__name", "competition__name")
    autocomplete_fields = ("school", "competition")
    actions = (disqualify_entries, requalify_entries, reset_scores)


@admin.register(StudentCompetitionEntry)
class StudentCompetitionEntryAdmin(BaseTimestampedAdmin):
    list_display = ("student_display", "competition", "score", "rank", "disqualified", "is_active", "created_at")
    list_filter = ("competition", "disqualified", "is_active")
    search_fields = (
        "student__user__username",
        "student__user__first_name",
        "student__user__last_name",
        "competition__name",
    )
    autocomplete_fields = ("student", "competition")
    actions = (disqualify_entries, requalify_entries, reset_scores)

    def student_display(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username
    student_display.short_description = "Student"


@admin.register(CompetitionScoreEvent)
class CompetitionScoreEventAdmin(BaseTimestampedAdmin):
    list_display = ("competition", "target_display", "points", "category", "created_by", "created_at")
    list_filter = ("competition", "category", "created_by")
    search_fields = (
        "competition__name",
        "school__name",
        "student__user__username",
        "student__user__first_name",
        "student__user__last_name",
        "reason",
    )
    autocomplete_fields = ("competition", "school", "student", "created_by")
    readonly_fields = ("created_at", "updated_at")

    def target_display(self, obj):
        if obj.school_id:
            return f"School: {obj.school.name}"
        if obj.student_id:
            name = obj.student.user.get_full_name() or obj.student.user.username
            return f"Student: {name}"
        return "-"
    target_display.short_description = "Target"


@admin.register(CompetitionDisqualification)
class CompetitionDisqualificationAdmin(BaseTimestampedAdmin):
    list_display = ("competition", "target_display", "reason", "created_by", "created_at")
    list_filter = ("competition", "created_by")
    search_fields = (
        "competition__name",
        "school__name",
        "student__user__username",
        "student__user__first_name",
        "student__user__last_name",
        "reason",
    )
    autocomplete_fields = ("competition", "school", "student", "created_by")
    readonly_fields = ("created_at", "updated_at")

    def target_display(self, obj):
        if obj.school_id:
            return f"School: {obj.school.name}"
        if obj.student_id:
            name = obj.student.user.get_full_name() or obj.student.user.username
            return f"Student: {name}"
        return "-"
    target_display.short_description = "Target"
