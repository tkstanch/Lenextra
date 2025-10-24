from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction

from .models import (
    University, College, StudentProfile,
    OrganizationTask, TaskApplication, TaskSubmission, StudentAchievement,
    OrganizationStudentTracking,
)
from .forms import (
    UniversityForm, CollegeForm, StudentProfileForm, TaskApplyForm, SubmissionForm,
    OrganizationStudentTrackingForm,
)

# Universities
@staff_member_required
def university_list(request):
    universities = University.objects.all().order_by("name")
    return render(request, "organizations/universities_list.html", {"universities": universities})

@staff_member_required
def university_create(request):
    if request.method == "POST":
        form = UniversityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "University created.")
            return redirect("organizations:university_list")
    else:
        form = UniversityForm()
    return render(request, "organizations/university_form.html", {"form": form})

@staff_member_required
def university_update(request, pk: int):
    obj = get_object_or_404(University, pk=pk)
    if request.method == "POST":
        form = UniversityForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "University updated.")
            return redirect("organizations:university_list")
    else:
        form = UniversityForm(instance=obj)
    return render(request, "organizations/university_form.html", {"form": form})

# Colleges
@staff_member_required
def college_list(request):
    colleges = College.objects.all().order_by("name")
    return render(request, "organizations/colleges_list.html", {"colleges": colleges})

@staff_member_required
def college_create(request):
    if request.method == "POST":
        form = CollegeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "College created.")
            return redirect("organizations:college_list")
    else:
        form = CollegeForm()
    return render(request, "organizations/college_form.html", {"form": form})

@staff_member_required
def college_update(request, pk: int):
    obj = get_object_or_404(College, pk=pk)
    if request.method == "POST":
        form = CollegeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "College updated.")
            return redirect("organizations:college_list")
    else:
        form = CollegeForm(instance=obj)
    return render(request, "organizations/college_form.html", {"form": form})

# Student profile (self-service)
@login_required
def student_profile_edit(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved.")
            return redirect("organizations:student_profile_edit")
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, "organizations/student_profile_form.html", {"form": form})

# Public tasks list and apply
def tasks_public_list(request):
    tasks = OrganizationTask.objects.filter(is_active=True, status="open").select_related("business")
    return render(request, "organizations/tasks_public_list.html", {"tasks": tasks})

@login_required
@transaction.atomic
def task_apply(request, task_id: int):
    task = get_object_or_404(OrganizationTask, pk=task_id, is_active=True, status="open")
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = TaskApplyForm(request.POST)
        if form.is_valid():
            motivation = form.cleaned_data.get("motivation") or ""
            app, created = TaskApplication.objects.get_or_create(task=task, student=profile, defaults={"motivation": motivation})
            if not created:
                app.motivation = motivation or app.motivation
                app.save(update_fields=["motivation"])
            messages.success(request, "Applied successfully." if created else "Application updated.")
            return redirect("organizations:applications")
    else:
        form = TaskApplyForm()
    # Fallback render if someone hits GET on apply URL
    return render(request, "organizations/tasks_public_list.html", {"tasks": [task], "form": form})

# My applications
@login_required
def applications_list(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    apps = TaskApplication.objects.filter(student=profile).select_related("task", "task__business").order_by("-created_at")
    return render(request, "organizations/applications_list.html", {"applications": apps})

# Submit work
@login_required
@transaction.atomic
def submit_work(request, application_id: int):
    application = get_object_or_404(TaskApplication, pk=application_id, student__user=request.user)
    submission = getattr(application, "submission", None)
    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.application = application
            obj.status = "submitted"
            obj.save()
            messages.success(request, "Submission saved.")
            return redirect("organizations:applications")
    else:
        form = SubmissionForm(instance=submission)
    return render(request, "organizations/submission_form.html", {"form": form})

# Achievements
@login_required
def achievements_list(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    achievements = StudentAchievement.objects.filter(student=profile).select_related("business", "task").order_by("-issued_at")
    return render(request, "organizations/achievements_list.html", {"achievements": achievements})

# Tracking students
@staff_member_required
def tracked_students_list(request):
    qs = (
        OrganizationStudentTracking.objects
        .select_related("student__user", "business", "student__university", "student__college")
        .order_by("-updated_at")
    )
    return render(request, "organizations/tracked_students_list.html", {"trackings": qs})

@staff_member_required
def track_student(request, pk: int | None = None):
    obj = get_object_or_404(OrganizationStudentTracking, pk=pk) if pk else None
    if request.method == "POST":
        form = OrganizationStudentTrackingForm(request.POST, instance=obj)
        if form.is_valid():
            tracking = form.save(commit=False)
            if not tracking.assigned_staff:
                tracking.assigned_staff = request.user
            tracking.save()
            messages.success(request, "Tracking saved.")
            return redirect("organizations:tracked_students")
    else:
        form = OrganizationStudentTrackingForm(instance=obj)
    return render(request, "organizations/track_student_form.html", {"form": form})
