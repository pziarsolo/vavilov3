"""
Django settings for vavilov3_web project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from corsheaders.defaults import default_headers
from _datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'i)^!7-o8zdtz1(kba*k(15pe6qwqsx*nl$+9)biux2irb)d)e*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'corsheaders',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'vavilov3',
    'django_celery_results',
    'drf_yasg']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vavilov3_web.urls'

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

WSGI_APPLICATION = 'vavilov3_web.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_crf_db',
        'USER': 'crf_user',
        'HOST': 'localhost',
        'PASSWORD': 'crf_pass'
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
VALIDATION_MODULE = 'django.contrib.auth.password_validation'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': VALIDATION_MODULE + '.UserAttributeSimilarityValidator'},
    {'NAME': VALIDATION_MODULE + '.MinimumLengthValidator'},
    {'NAME': VALIDATION_MODULE + '.CommonPasswordValidator'},
    {'NAME': VALIDATION_MODULE + '.NumericPasswordValidator'}
]
AUTH_USER_MODEL = 'vavilov3.User'
# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

# AUTH_USER_MODEL = 'vavilov3.User'
CORS_ORIGIN_WHITELIST = ('localhost:4200',)
CORS_ALLOW_HEADERS = default_headers + ('authentication', 'Authorization')
CORS_EXPOSE_HEADERS = ['Link', 'X-Total-Count']
CORS_ALLOW_METHODS = ('DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT')

REST_AUTHENTICATION_CLASSES = [
    'rest_framework_simplejwt.authentication.JWTAuthentication']

if True:  # DEVELOPMENT_MACHINE:
    REST_AUTHENTICATION_CLASSES.append(
        'rest_framework.authentication.SessionAuthentication')

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS':
        ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': REST_AUTHENTICATION_CLASSES
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1)
}

# celery
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_BACKEND_DB = 'postgresql://..'
CELERY_BROKER_URL = 'amqp:///'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
