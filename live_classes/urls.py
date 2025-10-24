from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views

app_name = "live_classes"
urlpatterns = [
    path("my/", login_required(TemplateView.as_view(template_name="live_classes/live_class_list.html")), name="my_list"),
    path("sessions/<int:pk>/join/", views.join_session, name="join"),  # NEW gated join
]