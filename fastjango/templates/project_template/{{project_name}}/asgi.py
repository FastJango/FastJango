"""
ASGI config for {{project_name}} project.
"""

import os
from fastjango.core.asgi import get_asgi_application

os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "{{project_name_snake}}.settings")

application = get_asgi_application() 