"""
API URLs for {{project_name}} project.
"""

from fastjango.urls import path
from fastjango.http import JsonResponse

def api_root(request):
    return JsonResponse({"message": "{{project_name}} API v1.0"})

urlpatterns = [
    path("/", api_root),
] 