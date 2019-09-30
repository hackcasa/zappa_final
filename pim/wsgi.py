"""
WSGI config for pim project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# add the hellodjango project path into the sys.path
sys.path.append('/var/www/pim/')
# add the virtualenv site-packages path to the sys.path
sys.path.append('/venvs/pim/lib/python3.6/site-packages')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pim.settings')

application = get_wsgi_application()
