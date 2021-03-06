# pinax.wsgi is configured to live in projects/pinaxdemosocial/deploy.

import os
import sys

from os.path import abspath, dirname, join
from site import addsitedir

addsitedir(abspath(join(dirname(__file__), "../../pinax-env/lib/python2.5/site-packages")))

sys.path.insert(0, abspath(join(dirname(__file__), "../../")))

from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "pinaxdemosocial.settings"

sys.path.insert(0, join(settings.PROJECT_ROOT, "apps"))

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
