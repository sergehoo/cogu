import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': config('DATABASE_NAME', default='cogu'),
#         'USER': config('DATABASE_USER', default='postgres'),
#         'PASSWORD': config('DATABASE_PASSWORD', default='postgres'),
#         'HOST': config('DATABASE_HOST', default='localhost'),
#         'PORT': config('DATABASE_PORT', default='5433'),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cogu',
        'USER': 'postgres',
        'PASSWORD': 'weddingLIFE18',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH', '/opt/homebrew/opt/gdal/lib/libgdal.dylib')
GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH', '/opt/homebrew/opt/geos/lib/libgeos_c.dylib')

MPI_API_KEY = os.getenv('MPI_API_KEY', default='key')

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = os.environ.get("EMAIL_HOST")
# EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
# # EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
# EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "True") == "True"
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtppro.orange.ci'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
# EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'no-reply@cogu.ci'
EMAIL_HOST_PASSWORD = 'weddingLIFE@18'
