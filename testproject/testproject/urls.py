"""
URL configuration for testproject project.
"""

from fastjango.urls import path, include
from fastjango.http import JsonResponse

# Define API endpoints
def index(request):
    return JsonResponse({"message": "Welcome to testproject"})

urlpatterns = [
    path("/", index),
    path("/api", include("testproject.api.urls")),
] 