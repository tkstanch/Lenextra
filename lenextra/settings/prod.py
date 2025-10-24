import os
from pathlib import Path
import dj_database_url

from .base import *

DEBUG = False

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)

# Safety: ensure NAME is str for non-sqlite backends
if DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
    name = DATABASES["default"].get("NAME")
    if isinstance(name, Path):
        DATABASES["default"]["NAME"] = str(name)

ADMINS = [
    ('Takudzwa Stanley Katsande', 'tkstanchxr1998@gmail.com'),
]

ALLOWED_HOSTS = ['.educaproject.com']

REDIS_URL = 'redis://cache:6379'
CACHES['default']['LOCATION'] = REDIS_URL
CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [REDIS_URL]