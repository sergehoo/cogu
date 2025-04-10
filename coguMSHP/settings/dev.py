import os

from decouple import config, Csv

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH', '/opt/homebrew/opt/gdal/lib/libgdal.dylib')
GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH', '/opt/homebrew/opt/geos/lib/libgeos_c.dylib')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DATABASE_NAME', default='rage'),
        'USER': config('DATABASE_USER', default='postgres'),
        'PASSWORD': config('DATABASE_PASSWORD', default='postgres'),
        'HOST': config('DATABASE_HOST', default='localhost'),
        'PORT': config('DATABASE_PORT', default='5433'),
    }
}

MPI_API_KEY = config('MPI_API_KEY', default='key')
