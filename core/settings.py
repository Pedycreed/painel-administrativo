"""
Django settings for core project.

Tudo que é sensível ou varia entre dev/prod vem de variável de ambiente.
Veja `.env.example` pras envs esperadas.
"""

from pathlib import Path
import os
from datetime import timedelta

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega .env do diretório do projeto (em prod, as envs vêm da plataforma)
load_dotenv(BASE_DIR / '.env')


# ============================================================
# Helpers
# ============================================================
def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name, '').strip().lower()
    if not val:
        return default
    return val in ('1', 'true', 'yes', 'on')


def _env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(name, '').strip()
    if not raw:
        return default or []
    return [item.strip() for item in raw.split(',') if item.strip()]


# ============================================================
# Core
# ============================================================
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    # Fallback inseguro APENAS pra dev local sem .env. Em prod, sempre setar.
    'django-insecure--ga718m&7_sqrx12w5++d90fi+&k1kau_pqej!(zmla1osn7f=',
)

DEBUG = _env_bool('DJANGO_DEBUG', default=True)

ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Hosts que o Django reconhece pra montar URLs absolutas (CSRF, etc).
# Em prod, listar o domínio do Railway + Vercel.
CSRF_TRUSTED_ORIGINS = _env_list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])


# ============================================================
# Apps + middleware
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'catalog',
    'accounts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serve os arquivos estáticos do Django em prod (admin, etc).
    # Precisa vir logo depois do SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ============================================================
# CORS
# ============================================================
# Em dev: localhost. Em prod: domínio do Vercel (setado via env).
CORS_ALLOWED_ORIGINS = _env_list(
    'DJANGO_CORS_ALLOWED_ORIGINS',
    default=[
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        # BiToons (site público)
        'https://bitoons.xyz',
        'https://www.bitoons.xyz',
        # WindScan (site público)
        'https://windscan.xyz',
        'https://www.windscan.xyz',
        # Vercel deploys
        'https://painel-administrativo-omega.vercel.app',
        'https://bitoons-i0k9txprs-painelex-s-projects.vercel.app',
        'https://windscan-156ptzoq7-painelex-s-projects.vercel.app',
    ],
)
# Permitir qualquer origem Vercel (preview deployments)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# ============================================================
# URLs / templates / WSGI
# ============================================================
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'


# ============================================================
# Database
# ============================================================
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ============================================================
# Auth
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.Usuario'


# ============================================================
# i18n
# ============================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# ============================================================
# Static files
# ============================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # `collectstatic` joga tudo aqui
# WhiteNoise comprime e adiciona hash nos arquivos pra cache forte
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media local não é usado em prod (imagens vão pro R2), mas mantém pro dev
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# DRF + JWT
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# ============================================================
# Segurança em produção
# ============================================================
# Quando DEBUG=False (prod), liga os headers de segurança.
# Railway/Vercel servem HTTPS automático, então redirect e cookies seguros valem.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 dias
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
