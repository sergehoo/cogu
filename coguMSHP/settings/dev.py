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
