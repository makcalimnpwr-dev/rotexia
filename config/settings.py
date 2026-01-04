import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Environment variable'dan al, yoksa varsayılan kullan (sadece development için)
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# Production'da mutlaka DEBUG=False olmalı!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Allowed hosts - Production'da mutlaka belirtilmeli
# Subdomain desteği için wildcard kullanılabilir
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# CSRF Trusted Origins - Subdomain'ler için wildcard destek
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app', 
    'https://*.ngrok-free.dev',
    'https://lynwood-gateless-emile.ngrok-free.dev', # Garanti olsun diye tam adresi de ekledik
    'https://*.onrender.com',  # Render wildcard subdomain desteği
]

# Subdomain Multi-Tenancy Ayarları
# Production'da domain belirtilmeli, development'ta None (localhost için)
SUBDOMAIN_DOMAIN = os.getenv('SUBDOMAIN_DOMAIN', None)  # Örn: 'fieldops.com' veya None

# Session Cookie Domain
# Production'da: '.fieldops.com' (tüm subdomain'lerde çalışır, ama daha az güvenli)
# Development'ta: None (her subdomain kendi session'ını kullanır, DAHA GÜVENLİ)
if SUBDOMAIN_DOMAIN and not DEBUG:
    SESSION_COOKIE_DOMAIN = f'.{SUBDOMAIN_DOMAIN}'  # Production
    CSRF_COOKIE_DOMAIN = f'.{SUBDOMAIN_DOMAIN}'  # Production
else:
    SESSION_COOKIE_DOMAIN = None  # Development (her subdomain kendi session'ı)
    CSRF_COOKIE_DOMAIN = None  # Development

# --- TWA (Trusted Web Activity) / Digital Asset Links ---
# Play Store'a TWA ile çıkmak için Android uygulama paket adı ve SHA256 sertifika fingerprint gerekir.
# TWA_PACKAGE_NAME: örn "com.sirket.fieldops"
# TWA_SHA256_FINGERPRINTS: virgülle ayrılmış, örn "AA:BB:...,11:22:..."
TWA_PACKAGE_NAME = os.getenv('TWA_PACKAGE_NAME', '')
TWA_SHA256_FINGERPRINTS = [s.strip() for s in os.getenv('TWA_SHA256_FINGERPRINTS', '').split(',') if s.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Buraya ekleyin:
    'apps.core', 
    'apps.users',
    'apps.customers',
    'apps.field_operations',
    'apps.forms',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Multi-Tenancy Middleware (en sonda, böylece diğer middleware'ler tenant'a erişebilir)
    'apps.core.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Global template klasörü
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ÖZEL CONTEXT PROCESSOR (Ayarları her sayfaya gömer)
                'apps.core.context_processors.site_settings',
                # Tenant context processor
                'apps.core.context_processors.tenant_context',
                # Kullanıcı yetki helper'ları (root admin vb.)
                'apps.users.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Production'da PostgreSQL kullanılmalı
DATABASE_URL = os.getenv('DATABASE_URL', None)

if DATABASE_URL:
    # PostgreSQL için (production)
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL)
        }
    except ImportError:
        # dj-database-url yüklü değilse SQLite kullan
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db_yeni.sqlite3',
            }
        }
else:
    # SQLite (development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_yeni.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# Internationalization
LANGUAGE_CODE = 'tr-tr' # Türkçe
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Django 5+: storage config
STORAGES = {
    "staticfiles": {
        # Manifest mode can cause 500s if any static entry is missing in production.
        # For demo stability on Render, use non-manifest compressed storage.
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# If manifest storage is enabled later, don't hard-fail on missing entries.
WHITENOISE_MANIFEST_STRICT = False

# Media files (Yüklenen logolar vs.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Jazzmin Ayarları (Admin Paneli Özelleştirme)
JAZZMIN_SETTINGS = {
    "site_title": "Rotexia Admin",
    "site_header": "Operasyon Yönetimi",
    "welcome_sign": "Yönetim Paneline Hoşgeldiniz",
    "search_model": "users.CustomUser",
    "show_ui_builder": True, # Canlı tema düzenleyiciyi açar
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# config/settings.py en alt satıra ekle:

LOGIN_REDIRECT_URL = 'home'  # Giriş yapınca anasayfaya at
LOGOUT_REDIRECT_URL = 'login' # Çıkış yapınca giriş ekranına at

# ============================================================================
# PRODUCTION GÜVENLİK AYARLARI
# ============================================================================

# HTTPS Ayarları (Production'da aktif olmalı)
if not DEBUG:
    # Render gibi reverse proxy arkasında HTTPS algısı için
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Email Ayarları (Production'da yapılandırılmalı)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@rotexia.com')