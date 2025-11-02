from django.urls import path
from . import views

app_name = 'arduino_projects'
urlpatterns = [
    path('edit/', views.editor, name='editor'),
    path('edit/<int:pk>/', views.editor, name='editor'),
    path('list/', views.project_list, name='project_list'),
    path('detail/<int:pk>/', views.project_detail, name='project_detail'),
    path('delete/<int:pk>/', views.project_confirm_delete, name='project_confirm_delete'),
    path('share/<int:pk>/', views.share_project, name='share_project'),
    path('download/<int:pk>/', views.download_file, name='download_file'),
    path('upload/<int:pk>/', views.upload_to_device, name='upload_to_device'),
]