from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered
from django.db import models
from .models import University, College, OrganizationTask, TaskApplication, TaskSubmission, StudentAchievement

class BaseTimestampedAdmin(admin.ModelAdmin):
    # Safe defaults so autocomplete_fields checks pass
    search_fields = ("id",)  # minimal valid default
    readonly_fields = ()     # avoid assuming created_at/updated_at

    def get_readonly_fields(self, request, obj=None):
        model_fields = {f.name for f in self.model._meta.get_fields() if getattr(f, "concrete", False)}
        dynamic = [n for n in ("created_at", "updated_at") if n in model_fields]
        return tuple(dynamic) + tuple(super().get_readonly_fields(request, obj))

    def get_search_fields(self, request):
        # If a subclass set its own search_fields, honor it
        if getattr(self, "search_fields", None) and self.search_fields != ("id",):
            return super().get_search_fields(request)

        # Heuristic: add common text fields to make autocomplete useful
        names = []
        text_fields = []
        for f in self.model._meta.get_fields():
            if getattr(f, "concrete", False):
                if isinstance(f, (models.CharField, models.TextField)):
                    text_fields.append(f.name)
        # Prefer typical labels if present
        for preferred in ("name", "title", "code"):
            if preferred in text_fields:
                names.append(preferred)
        # Fallback: first couple of text fields
        for n in text_fields:
            if n not in names:
                names.append(n)
        # Also allow searching by related user if present
        if any(f.name == "user" for f in self.model._meta.get_fields()):
            names = ["user__username", "user__email", "user__first_name", "user__last_name"] + names
        return tuple(names or ("id",))

class NameSearchAdmin(admin.ModelAdmin):
    search_fields = ("name",)

def maybe_register(model_name: str, admin_class=None):
    try:
        Model = apps.get_model("organizations", model_name)
    except LookupError:
        return
    try:
        if admin_class:
            admin.site.register(Model, admin_class)
        else:
            admin.site.register(Model)
    except AlreadyRegistered:
        pass

for name in ["StudentProfile", "Business", "School", "Partnership", "BusinessStudentTracking"]:
    maybe_register(name, BaseTimestampedAdmin)
for name in ["IndustryTag", "SkillTag"]:
    maybe_register(name, NameSearchAdmin)

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "country", "is_active", "created_at")
    search_fields = ("name", "slug", "city", "country")
    list_filter = ("is_active", "country")

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "country", "is_active", "created_at")
    search_fields = ("name", "slug", "city", "country")
    list_filter = ("is_active", "country")

@admin.register(OrganizationTask)
class OrganizationTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "business", "title", "status", "points", "deadline", "is_active", "created_at")
    list_filter = ("status", "is_active", "business")
    search_fields = ("title", "business__name", "slug")
    filter_horizontal = ("required_skills",)

@admin.register(TaskApplication)
class TaskApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "student", "status", "created_at")
    list_filter = ("status", "task__business")
    search_fields = ("task__title", "student__user__username")

@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "status", "reviewed_by", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("application__task__title",)

@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "business", "title", "points", "issued_at")
    list_filter = ("business",)
    search_fields = ("student__user__username", "title")