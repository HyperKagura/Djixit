"""
ASGI config for djixit project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os
from .settings import PRODUCTION

if PRODUCTION:
    import django
    from channels.routing import get_default_application

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djixit.settings')

    django.setup()

    application = get_default_application()
else:
    from django.core.asgi import get_asgi_application

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djixit.settings')

    application = get_asgi_application()

