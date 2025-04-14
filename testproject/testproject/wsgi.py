"""
WSGI config for testproject project.
"""

import os
from fastjango.core.wsgi import get_wsgi_application

os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "testproject.settings")

application = get_wsgi_application() 