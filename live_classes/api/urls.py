from django.urls import path
from .views import CreateLiveClassRequestAPIView, MyLiveSessionsAPIView, ScheduleLiveClassAPIView

app_name = "live_api"
urlpatterns = [
    path("requests/", CreateLiveClassRequestAPIView.as_view(), name="request_create"),
    path("sessions/", MyLiveSessionsAPIView.as_view(), name="my_sessions"),
    path("sessions/schedule/", ScheduleLiveClassAPIView.as_view(), name="schedule"),
]