"""
Django settings for attendance_system project.
"""
import os
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load configuration from config.yaml
CONFIG_FILE = BASE_DIR / 'config.yaml'
CONFIG = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, 'r') as f:
        try:
            CONFIG = yaml.safe_load(f)
        except yaml.YAMLError:
            pass

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY and not CONFIG.get('app', {}).get('secret_key'):
    # In production, this should fail immediately if key is missing
    if not os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 't'):
        raise ValueError("DJANGO_SECRET_KEY must be set in production.")
    SECRET_KEY = 'django-insecure-replace-me-in-development'
elif not SECRET_KEY:
    SECRET_KEY = CONFIG.get('app', {}).get('secret_key')

DEBUG = os.environ.get(
    'DJANGO_DEBUG', 
    str(CONFIG.get('app', {}).get('debug', 'False'))
).lower() in ('true', '1', 't')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    ALLOWED_HOSTS = CONFIG.get('app', {}).get('allowed_hosts', [])

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h and h != '*']
    if not ALLOWED_HOSTS:
        raise ValueError("DJANGO_ALLOWED_HOSTS must be set in production.")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    'django_filters',
    'axes',
    'channels',
    # Local apps
    'apps.accounts',
    'apps.employees',
    'apps.attendance',
    'apps.reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'attendance_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'attendance_system.wsgi.application'
ASGI_APPLICATION = 'attendance_system.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': os.environ.get(
            'DB_ENGINE', 
            CONFIG.get('database', {}).get('engine', 'django.db.backends.sqlite3')
        ),
        'NAME': os.environ.get(
            'DB_NAME', 
            CONFIG.get('database', {}).get('name', 'db.sqlite3') if CONFIG.get('database', {}).get('engine') == 'django.db.backends.sqlite3' else 'attendance_db'
        ),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Handle absolute path for sqlite3 name if relative
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    db_name = DATABASES['default']['NAME']
    if not os.path.isabs(db_name):
        DATABASES['default']['NAME'] = str(BASE_DIR / db_name)

# Channel layer for WebSockets
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.environ.get('REDIS_HOST', '127.0.0.1'), int(os.environ.get('REDIS_PORT', 6379)))],
        },
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication URLs
LOGIN_URL = 'login-page'
LOGIN_REDIRECT_URL = 'dashboard'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Attendance settings
ATTENDANCE_CONFIG = {
    'grace_period': int(os.environ.get('ATTENDANCE_GRACE_PERIOD', 15)),
    'late_limit': int(os.environ.get('ATTENDANCE_LATE_LIMIT', 60)),
}

# Authentication Backend
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Axes Configuration
AXES_FAILURE_LIMIT = int(os.environ.get('AXES_FAILURE_LIMIT', 5))
AXES_COOLOFF_TIME = float(os.environ.get('AXES_COOLOFF_TIME', 0.5))  # Hours
AXES_LOCKOUT_TEMPLATE = None  # Returns 403 by default for API
AXES_RESET_ON_SUCCESS = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'structured': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.environ.get('DJANGO_LOG_FILE', str(BASE_DIR / 'logs' / 'django.log')),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
LOGS_DIR = os.path.dirname(LOGGING['handlers']['file']['filename'])
if not os.path.exists(LOGS_DIR):
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except OSError:
        pass


