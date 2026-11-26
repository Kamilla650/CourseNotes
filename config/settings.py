"""Настройки проекта CourseNotes."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные из файла .env, расположенного в корне проекта
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-insecure-key')

# Строка из .env приводится к логическому значению
DEBUG = os.getenv('DEBUG', 'False').strip().lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'core',
    'accounts',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

# Database

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
    )
}

# Ключ ИИ-провайдера загружается из .env
AI_API_KEY = os.getenv('AI_PROVIDER_API_KEY')

# Своя модель пользователя (таблица users)
AUTH_USER_MODEL = 'core.User'


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# Static and media files

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'profile'
LOGOUT_REDIRECT_URL = 'login'

# --- Почта ---
# По умолчанию письма выводятся в консоль (для разработки и тестов)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
# Яндекс: smtp.yandex.ru, Mail.ru: smtp.mail.ru
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.yandex.ru')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True').strip().lower() in ('1', 'true', 'yes')  # обязательно для порта 465
EMAIL_USE_TLS = False  # TLS отключён, так как используется SSL
EMAIL_TIMEOUT = 10  # секунд, чтобы страница не зависала при недоступном сервере
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
# Здесь указывается ПАРОЛЬ ПРИЛОЖЕНИЯ из настроек почты, а не основной пароль ящика
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'noreply@coursenotes.local'

# Время жизни ссылки для сброса пароля, минут
PASSWORD_RESET_MINUTES = 30


# --- Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# --- JWT (simplejwt) ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
# --- Настройки ИИ-агента ---
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1')
LLM_API_KEY = os.getenv('LLM_API_KEY', 'ollama')
LLM_MODEL = os.getenv('LLM_MODEL', 'study-agent')
LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '300'))
LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '512'))