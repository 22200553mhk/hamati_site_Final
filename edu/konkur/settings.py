# konkur/settings.py

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# کلید امنیتی خود را اینجا قرار دهید
SECRET_KEY = 'django-insecure-your-secret-key-goes-here'

DEBUG = True

# مقدار صحیح که شما مشخص کردید، اینجا قرار گرفته است
ALLOWED_HOSTS = ['127.0.0.1', 'planikaa.ir', '185.231.112.23']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # برنامه شما
    'analyzer',

    # برنامه‌های مورد نیاز برای Allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Providerهای ورود (مثلاً گوگل)
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware مورد نیاز برای Allauth
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'konkur.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'konkur.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Allauth Configurations ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True

LOGIN_REDIRECT_URL = 'user_profile'
LOGOUT_REDIRECT_URL = 'dashboard'

# نکته: برای فعال‌سازی نهایی باید Client ID و Secret را از پنل توسعه‌دهندگان گوگل و مایکروسافت دریافت کنید
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'YOUR-GOOGLE-CLIENT-ID',
            'secret': 'YOUR-GOOGLE-SECRET-KEY',
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}