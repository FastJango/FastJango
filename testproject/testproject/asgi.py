"""
ASGI config for testproject project.
"""

import os
from fastjango.core.asgi import get_asgi_application

os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "testproject.settings")

application = get_asgi_application() 