from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from courses.views import CourseListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('courses/', include('courses.urls')),
    path('organizations/', include('organizations.urls')),
    path('', CourseListView.as_view(), name='course_list'),
    path('students/', include('students.urls')),
    path('parents/', include('parents.urls')),
    path('competitions/', include('competitions.urls')),
    path('api/', include('courses.api.urls', namespace='api')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('live/', include('live_classes.urls', namespace='live_classes')),
    path('api/live/', include('live_classes.api.urls', namespace='live_api')),
    path('api/orgs/', include('organizations.api.urls', namespace='org_api')),
    path('marketplace/', include('marketplace.urls')),  # Added marketplace URLs
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)