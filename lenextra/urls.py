"""
URL configuration for lenextra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from courses.views import CourseListView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views 
from django.urls import path, include


urlpatterns = [
    path(
        'accounts/login/', auth_views.LoginView.as_view(), name='login'
    ),
    path(
        'accounts/logout/', auth_views.LogoutView.as_view(), name='logout'
    ),
    path('admin/', admin.site.urls),
    path('courses/', include('courses.urls')),
    path('organizations/', include('organizations.urls')),
    path('', CourseListView.as_view(), name='course_list'),
    path('students/', include('students.urls')),
    path('parents/', include('parents.urls')),
    path('competitions/', include('competitions.urls')), # <-- add this
     path('api/', include('courses.api.urls', namespace='api')),
     path('chat/', include('chat.urls', namespace='chat')),
    path('__debug__/', include('debug_toolbar.urls')),
    path("payments/", include("payments.urls", namespace="payments")),
    path("live/", include("live_classes.urls", namespace="live_classes")),
    path("api/live/", include("live_classes.api.urls", namespace="live_api")),
    path("api/orgs/", include("organizations.api.urls", namespace="org_api")),
    path('labs/', include('practice_labs.urls')),
    path('api/labs/', include('practice_labs.api_urls')),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

