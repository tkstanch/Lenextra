from django.urls import path
from .views import landing

app_name = "competitions"

urlpatterns = [
    path("", landing, name="landing"),
]