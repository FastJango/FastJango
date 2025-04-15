
from fastjango.urls import path, include
from fastjango.http import JsonResponse

def index(request):
    return JsonResponse({"message": "Root view"})

def about(request):
    return JsonResponse({"message": "About view"})

urlpatterns = [
    path("/", index, name="index"),
    path("/about", about, name="about"),
    path("/app", include("tests.test_app.urls")),
    path("/nested", include("tests.nested_app.urls")),
    path("/edge", include("tests.edge_cases.urls")),
]
