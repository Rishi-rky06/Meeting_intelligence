"""
Base settings shared across all environments.
"""

import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'apps.authentication',
    'apps.meetings',
    'apps.analysis',
    'apps.action_items',
    'apps.reminders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware.TraceIDMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.authentication.middleware.JWTAuthMiddleware',
]

# CORS — allow all origins (assignment requirement: CORS enabled *)
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'authentication.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exceptions.global_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Meeting Intelligence Service API',
    'DESCRIPTION': 'AI-powered meeting intelligence platform for capturing insights, action items, and follow-ups.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    # Register the JWT Bearer scheme so the Swagger "Authorize" button works.
    # (Auth is enforced by custom middleware, so spectacular needs this hint.)
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'SECURITY': [{'BearerAuth': []}],
    # Give the two distinct "status" enums clear names instead of the
    # auto-generated collision name (e.g. "StatusFa9Enum"). Values are listed
    # inline because the choices live on nested TextChoices classes that an
    # import path can't reach.
    'ENUM_NAME_OVERRIDES': {
        'ActionItemStatusEnum': [
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
        ],
        'AnalysisStatusEnum': [
            ('PENDING', 'Pending'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
    },
}

JWT_SECRET_KEY = config('JWT_SECRET_KEY')
JWT_ACCESS_TOKEN_EXPIRY_HOURS = 1
JWT_REFRESH_TOKEN_EXPIRY_DAYS = 7
JWT_ALGORITHM = 'HS256'

GROQ_API_KEY = config('GROQ_API_KEY')
GROQ_MODEL = config('GROQ_MODEL', default='llama-3.3-70b-versatile')
GROQ_BASE_URL = config('GROQ_BASE_URL', default='https://api.groq.com/openai/v1')

RESEND_API_KEY = config('RESEND_API_KEY')
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='reminders@yourdomain.com')

SCHEDULER_INTERVAL_MINUTES = config('SCHEDULER_INTERVAL_MINUTES', default=30, cast=int)

CANDIDATE_NAME = config('CANDIDATE_NAME', default='Koushik Reddy Yeredla')
CANDIDATE_EMAIL = config('CANDIDATE_EMAIL', default='koushikreddyyeredla@gmail.com')
REPOSITORY_URL = config('REPOSITORY_URL', default='')
DEPLOYED_URL = config('DEPLOYED_URL', default='')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': 'core.logging_formatter.StructuredFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
