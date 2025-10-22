from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .models import (
    Competition,
    SchoolCompetitionEntry,
    StudentCompetitionEntry,
)
from .forms import (
    CompetitionForm,
    SchoolJoinForm,
    StudentJoinForm,
    ScorePointsForm,
    DisqualifyForm,
    LeaderboardFilterForm,
)

staff_required = user_passes_test(lambda u: u.is_staff)


def _paginate(request, qs, per_page=25, page_param="page"):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(request.GET.get(page_param))


# -------- Competitions --------
def competition_list(request):
    """
    List competitions with filters: q (name), status (upcoming|ongoing|finished|all), discipline id.
    """
    qs = Competition.objects.select_related("discipline").order_by("-start_date", "name")

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").lower()
    discipline_id = request.GET.get("discipline")

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if discipline_id:
        qs = qs.filter(discipline_id=discipline_id)

    # Status filter using date ranges
    from django.utils import timezone

    today = timezone.localdate()
    if status == "upcoming":
        qs = qs.filter(start_date__gt=today)
    elif status == "ongoing":
        qs = qs.filter(start_date__lte=today, end_date__gte=today)
    elif status == "finished":
        qs = qs.filter(end_date__lt=today)

    # Annotate counts
    qs = qs.annotate(
        school_count=Count("entries", distinct=True),
        student_count=Count("student_entries", distinct=True),
    )
    competitions = _paginate(request, qs, per_page=20)
    return render(
        request,
        "competitions/competition_list.html",
        {"competitions": competitions, "q": q, "status": status, "discipline_id": discipline_id},
    )


def competition_detail(request, slug):
    """
    Detail page with top entries and quick links.
    """
    comp = get_object_or_404(
        Competition.objects.select_related("discipline"), slug=slug
    )
    school_entries = comp.leaderboard_schools()
    student_entries = comp.leaderboard_students()

    school_entries_page = _paginate(request, school_entries, per_page=25, page_param="spage")
    student_entries_page = _paginate(request, student_entries, per_page=25, page_param="tpage")

    return render(
        request,
        "competitions/competition_detail.html",
        {
            "competition": comp,
            "school_entries": school_entries_page,
            "student_entries": student_entries_page,
        },
    )


@staff_required
def competition_create(request):
    if request.method == "POST":
        form = CompetitionForm(request.POST)
        if form.is_valid():
            comp = form.save()
            messages.success(request, "Competition created.")
            return redirect("competitions:competition_detail", slug=comp.slug)
    else:
        form = CompetitionForm()
    return render(request, "competitions/competition_form.html", {"form": form})


@staff_required
def competition_update(request, slug):
    comp = get_object_or_404(Competition, slug=slug)
    if request.method == "POST":
        form = CompetitionForm(request.POST, instance=comp)
        if form.is_valid():
            comp = form.save()
            messages.success(request, "Competition updated.")
            return redirect("competitions:competition_detail", slug=comp.slug)
    else:
        form = CompetitionForm(instance=comp)
    return render(request, "competitions/competition_form.html", {"form": form, "competition": comp})


@staff_required
def competition_delete(request, slug):
    comp = get_object_or_404(Competition, slug=slug)
    if request.method == "POST":
        comp.delete()
        messages.success(request, "Competition deleted.")
        return redirect("competitions:competition_list")
    return render(request, "competitions/competition_confirm_delete.html", {"competition": comp})


# -------- Participation (join) --------
@login_required
def join_school(request, slug):
    comp = get_object_or_404(Competition, slug=slug)
    if request.method == "POST":
        form = SchoolJoinForm(request.POST, competition=comp)
        if form.is_valid():
            form.save()
            messages.success(request, "School joined the competition.")
            return redirect("competitions:competition_detail", slug=comp.slug)
    else:
        form = SchoolJoinForm(competition=comp)
    return render(request, "competitions/join_school.html", {"form": form, "competition": comp})


@login_required
def join_student(request, slug):
    comp = get_object_or_404(Competition, slug=slug)
    if request.method == "POST":
        form = StudentJoinForm(request.POST, competition=comp)
        if form.is_valid():
            form.save()
            messages.success(request, "Student joined the competition.")
            return redirect("competitions:competition_detail", slug=comp.slug)
    else:
        form = StudentJoinForm(competition=comp)
    return render(request, "competitions/join_student.html", {"form": form, "competition": comp})


# -------- Scoring and Disqualifications --------
@staff_required
def score_points(request, slug):
    """
    Add points to a school or student entry (exactly one).
    """
    comp = get_object_or_404(Competition, slug=slug)
    if request.method == "POST":
        form = ScorePointsForm(request.POST, competition=comp)
        if form.is_valid():
            target = form.save(user=request.user)
            messages.success(request, f"Points updated for {target}.")
            return redirect("competitions:competition_detail", slug=comp.slug)
    else:
        form = ScorePointsForm(competition=comp)
    return render(request, "competitions/score_points.html", {"form": form, "competition": comp})


@staff_required
def disqualify_entry(request, slug):
    """
    Disqualify a school or student entry (exactly one).
    """
    comp = get_object_or_404(Competition, slug=slug)
    if request.method == "POST":
        form = DisqualifyForm(request.POST, competition=comp)
        if form.is_valid():
            target = form.save(user=request.user)
            messages.warning(request, f"Disqualified: {target}.")
            return redirect("competitions:competition_detail", slug=comp.slug)
    else:
        form = DisqualifyForm(competition=comp)
    return render(request, "competitions/disqualify.html", {"form": form, "competition": comp})


# -------- Leaderboards --------
def leaderboard_schools(request, slug):
    """
    Per-competition school leaderboard with filters.
    """
    comp = get_object_or_404(Competition, slug=slug)
    qs = SchoolCompetitionEntry.objects.select_related("school", "competition").filter(competition=comp)
    filter_form = LeaderboardFilterForm(request.GET or None)
    qs = filter_form.apply_to_school_qs(qs)
    entries = _paginate(request, qs.order_by("-score", "created_at"), per_page=50)
    return render(
        request,
        "competitions/leaderboard_schools.html",
        {"competition": comp, "entries": entries, "filter_form": filter_form},
    )


def leaderboard_students(request, slug):
    """
    Per-competition student leaderboard with filters.
    """
    comp = get_object_or_404(Competition, slug=slug)
    qs = StudentCompetitionEntry.objects.select_related("student__user", "student__school", "competition").filter(
        competition=comp
    )
    filter_form = LeaderboardFilterForm(request.GET or None)
    qs = filter_form.apply_to_student_qs(qs)
    entries = _paginate(request, qs.order_by("-score", "created_at"), per_page=50)
    return render(
        request,
        "competitions/leaderboard_students.html",
        {"competition": comp, "entries": entries, "filter_form": filter_form},
    )


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Competition  # adjust if different
try:
    from .forms import JoinCompetitionForm
except Exception:
    JoinCompetitionForm = None

@login_required
def landing(request):
    competitions = Competition.objects.all().order_by("-id")[:50]
    form = JoinCompetitionForm() if JoinCompetitionForm else None
    comp_id = request.GET.get("id")
    competition = competitions.filter(pk=comp_id).first() if comp_id else None
    return render(
        request,
        "competitions/landing.html",
        {"competitions": competitions, "form": form, "competition": competition},
    )
