import os

from id_manager.settings.base_public import *

ALLOWED_HOSTS = ["*"]

DEBUG = True


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default",
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    }
}

ACA_PY_URL = os.environ.get("ACA_PY_URL")
ACA_PY_TRANSPORT_URL = "http://0.0.0.0:8002"
ACA_PY_AUTH_TOKEN = ""

SITE_URL = "http://localhost:8082"
POLL_INTERVAL = 5000
POLL_MAX_TRIES = 12

EMAIL_HOST = os.environ.get("EMAIL_HOST")