from .settings.base import *  # reuse base

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "organizations.apps.OrganizationsConfig",
]

ROOT_URLCONF = "lenextra.urls_orgonly"