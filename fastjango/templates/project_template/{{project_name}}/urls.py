"""
URL configuration for {{project_name}} project.
"""

from fastjango.urls import path, include
from fastjango.http import JsonResponse

# Define API endpoints
def index(request):
    return JsonResponse({"message": "Welcome to {{project_name}}"})

urlpatterns = [
    path("/", index),
    path("/api", include("{{project_name_snake}}.api.urls")),
] 