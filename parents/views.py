from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import ParentProfile, StudentProgress
from .forms import StudentProgressForm


def _get_parent_profile(user):
    profile, _ = ParentProfile.objects.get_or_create(user=user)
    return (
        ParentProfile.objects.select_related("user")
        .prefetch_related("students__user")
        .get(pk=profile.pk)
    )


@login_required
def parent_dashboard(request):
    profile = _get_parent_profile(request.user)
    today = timezone.localdate()
    qs = (
        StudentProgress.objects.filter(parent=profile)
        .select_related("student__user")
        .order_by("-date", "-updated_at")
    )
    recent_progress = list(qs[:20])
    today_progress = list(qs.filter(date=today))

    form = StudentProgressForm(request.POST or None, parent=profile)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.parent = profile
        obj.save()
        return redirect("parents:dashboard")

    return render(
        request,
        "parents/dashboard.html",
        {
            "profile": profile,
            "students": profile.students.all(),
            "recent_progress": recent_progress,
            "today_progress": today_progress,
            "today": today,
            "form": form,
        },
    )


@login_required
def progress_list(request, student_id: int):
    profile = _get_parent_profile(request.user)
    student = get_object_or_404(profile.students.select_related("user"), pk=student_id)

    entries = (
        StudentProgress.objects.filter(parent=profile, student=student)
        .order_by("-date", "-updated_at")
    )

    # Filters
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    q = request.GET.get("q")

    if date_from:
        entries = entries.filter(date__gte=date_from)
    if date_to:
        entries = entries.filter(date__lte=date_to)
    if q:
        entries = entries.filter(Q(notes__icontains=q))

    # Totals
    totals = entries.aggregate(
        count=Count("id"),
        completed_lessons=Sum("completed_lessons"),
        time_spent_minutes=Sum("time_spent_minutes"),
        avg_score=Avg("average_score"),
        avg_progress=Avg("progress_percent"),
    )

    # Pagination
    paginator = Paginator(entries.select_related("student__user"), 25)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(
        request,
        "parents/progress_list.html",
        {
            "student": student,
            "entries": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.paginator.num_pages > 1,
            "totals": totals,
        },
    )


@login_required
def progress_add(request):
    profile = _get_parent_profile(request.user)
    form = StudentProgressForm(request.POST or None, parent=profile)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.parent = profile
        obj.save()
        return redirect("parents:progress_list", student_id=obj.student_id)
    return render(request, "parents/progress_form.html", {"form": form})


@login_required
def student_overview(request, student_id: int):
    profile = _get_parent_profile(request.user)
    # restrict to linked student
    student = get_object_or_404(profile.students.select_related("user"), pk=student_id)

    today = timezone.localdate()
    entries = StudentProgress.objects.filter(parent=profile, student=student)

    last7_from = today - timedelta(days=6)
    last30_from = today - timedelta(days=29)

    last7 = entries.filter(date__gte=last7_from)
    last30 = entries.filter(date__gte=last30_from)

    kpis = {
        "w_lessons": last7.aggregate(v=Coalesce(Sum("completed_lessons"), 0))["v"],
        "w_minutes": last7.aggregate(v=Coalesce(Sum("time_spent_minutes"), 0))["v"],
        "w_avg_score": last7.aggregate(v=Avg("average_score"))["v"],
        "w_avg_progress": last7.aggregate(v=Avg("progress_percent"))["v"],
        "m_lessons": last30.aggregate(v=Coalesce(Sum("completed_lessons"), 0))["v"],
        "m_minutes": last30.aggregate(v=Coalesce(Sum("time_spent_minutes"), 0))["v"],
    }

    # compute daily streak (consecutive days including today with any entry)
    dates_set = set(entries.values_list("date", flat=True))
    streak = 0
    d = today
    while d in dates_set:
        streak += 1
        d = d - timedelta(days=1)

    recent = entries.select_related("student__user").order_by("-date", "-updated_at")[:20]

    return render(
        request,
        "parents/student_overview.html",
        {
            "profile": profile,
            "student": student,
            "kpis": kpis,
            "streak": streak,
            "recent_entries": recent,
            "today": today,
        },
    )