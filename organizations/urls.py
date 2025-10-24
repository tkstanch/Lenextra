from django.urls import path
from . import views

app_name = "organizations"

urlpatterns = [
    # Universities
    path("universities/", views.university_list, name="university_list"),
    path("universities/create/", views.university_create, name="university_create"),
    path("universities/<int:pk>/edit/", views.university_update, name="university_update"),

    # Colleges
    path("colleges/", views.college_list, name="college_list"),
    path("colleges/create/", views.college_create, name="college_create"),
    path("colleges/<int:pk>/edit/", views.college_update, name="college_update"),

    # Student profile
    path("students/profile/", views.student_profile_edit, name="student_profile_edit"),

    # Tasks
    path("tasks/", views.tasks_public_list, name="tasks_public"),
    path("tasks/<int:task_id>/apply/", views.task_apply, name="task_apply"),
    path("applications/", views.applications_list, name="applications"),
    path("applications/<int:application_id>/submit/", views.submit_work, name="submit_work"),

    # Achievements
    path("achievements/", views.achievements_list, name="achievements"),

    # Tracked students
    path("tracked/", views.tracked_students_list, name="tracked_students"),
    path("tracked/create/", views.track_student, name="track_student"),
    path("tracked/<int:pk>/edit/", views.track_student, name="track_student_edit"),
]