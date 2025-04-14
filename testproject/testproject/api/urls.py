"""
API URLs for testproject project.
"""

from fastjango.urls import path
from fastjango.http import JsonResponse

def api_root(request):
    return JsonResponse({"message": "testproject API v1.0"})

urlpatterns = [
    path("/", api_root),
] 