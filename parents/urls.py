from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "parents"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="parents:dashboard", permanent=False), name="root"),
    path("dashboard/", views.parent_dashboard, name="dashboard"),
    path("students/<int:student_id>/progress/", views.progress_list, name="progress_list"),
    path("progress/add/", views.progress_add, name="progress_add"),
    path("students/<int:student_id>/overview/", views.student_overview, name="student_overview"),
]