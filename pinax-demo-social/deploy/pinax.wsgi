# pinax.wsgi is configured to live in projects/pinax-demo-social/deploy.

import os
import sys

from os.path import abspath, dirname, join
from site import addsitedir

addsitedir(abspath(join(dirname(__file__), "../../pinax-env/lib/python2.5/site-packages")))
addsitedir(abspath(join(dirname(__file__), "../../pinax-demo-social")))

sys.path.insert(0, abspath(join(dirname(__file__), "../../")))

from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "pinax-demo-social.settings"

sys.path.insert(0, join(settings.PROJECT_ROOT, "apps"))

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
