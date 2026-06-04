"""
Test settings — uses SQLite in-memory so tests run without a Postgres instance.
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

DISABLE_SCHEDULER = True

# Prevent scheduler from starting during tests
import os
os.environ['DISABLE_SCHEDULER'] = 'true'
