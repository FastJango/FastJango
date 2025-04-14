"""
WSGI config for {{project_name}} project.
"""

import os
from fastjango.core.wsgi import get_wsgi_application

os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "{{project_name_snake}}.settings")

application = get_wsgi_application() 