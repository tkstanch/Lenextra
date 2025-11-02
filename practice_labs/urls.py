from django.urls import path
from . import views

urlpatterns = [
    path('', views.lab_list, name='lab_list'),
    path('<int:lab_id>/step/<int:step_order>/', views.lab_detail, name='lab_detail'),
]