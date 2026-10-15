
from settings.conf import DB_NAME, DB_PASSWORD, DB_USER
from settings.env import *


DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': 'DB_HOST',
        'PORT': 'DB_PORT',
    }
}
