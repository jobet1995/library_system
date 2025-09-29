from .settings import *
import os

# Use a separate database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'test_library'),
        'USER': os.getenv('DB_USER', 'test_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'test_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'TEST': {
            'NAME': f"test_{os.getenv('DB_NAME', 'test_library')}",
        },
    }
}

# Use faster password hasher for testing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging for tests
import logging
logging.disable(logging.CRITICAL)

# Use in-memory cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Disable email sending during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable any external API calls
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable debug toolbar if used
DEBUG = False

# Disable any external services
PAYMENT_GATEWAY_ENABLED = False
EXTERNAL_API_ENABLED = False
