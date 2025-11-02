from django.urls import path
from . import api_views

urlpatterns = [
    path('labs/', api_views.LabListAPI.as_view(), name='api_lab_list'),
    path('steps/<int:pk>/', api_views.LabStepDetailAPI.as_view(), name='api_lab_step_detail'),
    path('progress/', api_views.UserLabProgressAPI.as_view(), name='api_lab_progress'),
]

urlpatterns += [
    path('steps/<int:step_id>/check/', api_views.StepCodeCheckAPI.as_view(), name='api_step_code_check'),
]