import os
import sys

dn = os.path.dirname
path = os.path.abspath( dn(dn(__file__)) )
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'app.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
