"""
Django settings for merge_integration project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
import boto3
from dotenv import load_dotenv
from merge_integration.utils import get_db_password

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")
ACCOUNT_TOKEN = os.getenv("ACCOUNT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
GETKLOO_BASE_URL = os.getenv("GETKLOO_BASE_URL")
GETKLOO_LOCAL_URL = os.getenv("GETKLOO_LOCAL_URL")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
SQS_QUEUE = os.environ.get("SQS_QUEUE")
SQS_BUCKET = os.environ.get("SQS_BUCKET")
MERGE_BASE_URL = os.environ.get("BASE_URL")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
# app = Celery("merge_integration")
# app.config_from_object("django.conf:settings", namespace="CELERY")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
APPEND_SLASH = False
ALLOWED_HOSTS = ["*"]
# app.autodiscover_tasks()
# CORS setting
CORS_ORIGIN_ALLOW_ALL = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://dev.getkloo.com",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "Authorization",
    "Cache-Control",
    "Content-Type",
    "Expires",
    "Referer",
    "User-Agent",
    "Accept",
    "Pragma",
]

# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_crontab",
    # 'django_celery_results',
    # 'django_celery_beat',
]

PROJECT_APPS = [
    "ACCOUNTS",
    "LINKTOKEN",
    "corsheaders",
    "TRACKING_CATEGORIES",
    "TAX_RATE",
    "COMPANY_INFO",
    "PURCHASE_ORDERS",
    "CONTACTS",
    "SYNC",
    "INVOICES",
    "merge_integration",
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "middleware.request_logger.RequestLogMiddleware",
]

ROOT_URLCONF = "merge_integration.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "merge_integration.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": get_db_password(os.getenv("RDS_HOST")) or os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("RDS_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cron jobs
CRONJOBS = [
    ("*/1 * * * *", "INVOICES.scheduled_tasks.daily_get_merge_invoice.main"),
    # ('*/2 * * * 1-5', 'django.core.management.call_command', ['create_pending_invoice_module']),
    ('*/2 * * * *', 'django.core.management.call_command', ['create_pending_invoice_module']),
]

# Define the path to the cron_logs directory
CRON_LOGS_DIR = BASE_DIR / 'INVOICES' / 'cron_logs'

# Ensure the cron_logs directory exists
if not CRON_LOGS_DIR.exists():
    CRON_LOGS_DIR.mkdir(parents=True, exist_ok=True)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': CRON_LOGS_DIR / 'invoices_cron.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

tracking_categories_page_size = 50
tracking_categories_batch_size = 50

accounts_page_size = 100
accounts_batch_size = 100

company_info_page_size = 50
company_info_batch_size = 50

contacts_page_size = 100
contacts_batch_size = 100

invoices_page_size = 50
invoices_batch_size = 50

tax_rate_page_size = 100
tax_rate_batch_size = 100

items_rate_page_size = 100
items_rate_batch_size = 100

SAGE_INTACCT_RETRIES = 12
SAGE_INTACCT_INTERVAL = 300

# CELERY_BROKER_URL = 'sqs://'

# CELERY_BROKER_URL = f'sqs://{AWS_ACCESS_KEY_ID}:{AWS_SECRET_ACCESS_KEY}@{AWS_DEFAULT_REGION}.amazonaws.com/{SQS_QUEUE}'
# CELERY_RESULT_BACKEND = 'django-db'


sqs_client = boto3.client(
    "sqs",
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
queue_url = sqs_client.get_queue_url(QueueName=SQS_QUEUE)["QueueUrl"]

CELERY_BROKER_URL = "sqs://"
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "region": AWS_DEFAULT_REGION,
    "polling_interval": 10,  # Adjust as needed
    "queue_name": queue_url,
    "is_secure": True,  # Set to True to use SigV4 authentication
}
broker_transport_options = {"wait_time_seconds": 10}

CELERY_RESULT_BACKEND = "django-db"
CELERY_TIMEZONE = "UTC"

TASK_QUEUE_NAME = "dev-bulk-data-import"
CELERY_TRACK_STARTED = True

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_CONTENT_ENCODING = "utf-8"
