from django.urls import path
from .views import (
    PublicTasksListAPIView, BusinessTasksListAPIView,
    ApplyToTaskAPIView, MyApplicationsAPIView,
    SubmitWorkAPIView, ReviewSubmissionAPIView,
    MyAchievementsAPIView,
)

app_name = "org_api"
urlpatterns = [
    path("tasks/", PublicTasksListAPIView.as_view(), name="tasks_public"),
    path("business/<int:business_id>/tasks/", BusinessTasksListAPIView.as_view(), name="tasks_business"),
    path("tasks/apply/", ApplyToTaskAPIView.as_view(), name="task_apply"),
    path("applications/", MyApplicationsAPIView.as_view(), name="my_applications"),
    path("applications/<int:application_id>/submit/", SubmitWorkAPIView.as_view(), name="submit_work"),
    path("submissions/<int:submission_id>/review/", ReviewSubmissionAPIView.as_view(), name="review_submission"),
    path("achievements/", MyAchievementsAPIView.as_view(), name="my_achievements"),
]