# FastJango

FastJango is a Django-inspired toolkit built on FastAPI. It gives you familiar Django-like primitives (URLs, middleware, forms, settings, pagination, a CLI) while leveraging FastAPI/Starlette performance.

## Features (implemented)

- [Django-like URL patterns and resolver](#urls-django-like) (`path`, `include`, `URLResolver`) · [module](/fastjango/urls.py)
- [HTTP helpers](#http-helpers): `HttpResponse`, `JsonResponse`, `redirect` · [module](/fastjango/http.py)
- [Middleware](#middleware): CORS and Security (Django-like configuration style) · [CORS](/fastjango/middleware/cors.py) · [Security](/fastjango/middleware/security.py)
- [Forms](#forms) with validation (Pydantic-powered) · [module](/fastjango/forms/forms.py)
- [Settings](#settings-django-like) (Django-like) and helpers (`configure_settings`, `get_settings_instance`) · [module](/fastjango/core/settings.py)
- [Pagination](#pagination) utilities (page number, limit/offset, cursor) with FastAPI integration · [package](/fastjango/pagination)
- [CLI](#cli-commands) project/app scaffolding and utilities · [entrypoint](/fastjango/cli/main.py)
- Experimental ORM and SQLAlchemy compatibility (APIs present; still evolving) · [ORM](/fastjango/db) · [SA compat](/fastjango/db/sqlalchemy_compat.py)

## Table of contents

- [Install](#install)
- [Quick start (CLI)](#quick-start-cli)
- [URLs (Django-like)](#urls-django-like)
- [HTTP helpers](#http-helpers)
- [Middleware](#middleware)
- [Forms](#forms)
- [Settings (Django-like)](#settings-django-like)
- [Pagination](#pagination)
- [CLI commands](#cli-commands)
- [Notes on the ORM](#notes-on-the-orm)
- [Built With](#built-with)
- [License](#license)

## Install

```bash
pip install fastjango
```

For local development of this repo:

```bash
git clone https://github.com/yourusername/fastjango.git
cd fastjango
pip install -e .
```

## Quick start (CLI)

```bash
# Create a project
fastjango-admin startproject myproject
cd myproject

# Create an app inside the project
fastjango-admin startapp myapp

# Run the dev server
fastjango-admin runserver
```

## URLs (Django-like)

See: [`fastjango.urls`](/fastjango/urls.py). Also refer to tests: [`tests/test_url_conf.py`](/tests/test_url_conf.py).

Define URL patterns using `path` and `include`, then register them on a FastAPI router via `URLResolver`.

```python
# urls.py
from fastapi import APIRouter
from fastjango.urls import path, include, URLResolver
from fastjango.http import JsonResponse

# Views
def index(request):
    return JsonResponse({"message": "Hello from FastJango"})

def item_detail(request, id):
    return JsonResponse({"id": id})

# Patterns
urlpatterns = [
    path("/", index, name="index"),
    path("/items/<int:id>", item_detail, name="item-detail"),
]

# Attach to FastAPI
router = APIRouter()
URLResolver(router).register(urlpatterns)
```

## HTTP helpers

See: [`fastjango/http.py`](/fastjango/http.py).

```python
from fastjango.http import HttpResponse, JsonResponse, redirect

# HTML/text
resp = HttpResponse("OK", status_code=200)  # content-type text/html by default

# JSON
resp = JsonResponse({"ok": True}, status_code=201)

# Redirects
resp = redirect("/login", permanent=False)  # 302 by default
```

## Middleware

See: [`fastjango/middleware/cors.py`](/fastjango/middleware/cors.py) and [`fastjango/middleware/security.py`](/fastjango/middleware/security.py). Example usage is also shown in [`test_pagination_and_cors.py`](/test_pagination_and_cors.py).

CORS and Security middleware mirror Django-style configuration while running on Starlette.

```python
from fastapi import FastAPI
from fastjango.middleware.cors import CORSMiddleware
from fastjango.middleware.security import SecurityMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allowed_origins=["https://example.com"],
    allow_credentials=True,
    allowed_methods=["GET", "POST"],
    allowed_headers=["Content-Type"],
)

# Security headers
app.add_middleware(
    SecurityMiddleware,
    secure_content_type_nosniff=True,
    secure_browser_xss_filter=True,
    secure_frame_deny=True,
)
```

## Forms

See: [`fastjango/forms/forms.py`](/fastjango/forms/forms.py).

Define forms declaratively and validate incoming data.

```python
from fastjango.forms import Form, CharField, EmailField, BooleanField, ValidationError

class ContactForm(Form):
    name = CharField(max_length=100)
    email = EmailField()
    message = CharField(max_length=500, required=False)
    subscribe = BooleanField(required=False)

form = ContactForm(data={
    "name": "Jane",
    "email": "jane@example.com",
    "message": "Hi!"
})

if form.is_valid():
    # Access cleaned data
    data = form.cleaned_data
else:
    # Field errors
    errors = form.errors
```

## Settings (Django-like)

See: [`fastjango/core/settings.py`](/fastjango/core/settings.py).

Use a global settings instance or configure at startup.

```python
from fastjango.core.settings import configure_settings, get_settings_instance

configure_settings({
    "DEBUG": True,
    "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
    "PAGINATION_PAGE_SIZE": 20,
})

settings = get_settings_instance()
print(settings.DEBUG)  # True
```

## Pagination

See: [`fastjango/pagination`](/fastjango/pagination). Full example API available in [`test_pagination_and_cors.py`](/test_pagination_and_cors.py).

Drop-in pagination helpers for FastAPI endpoints.

```python
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from fastapi import FastAPI, Request, Depends
from fastjango.pagination import (
    PageNumberPagination,
    get_page_number_pagination,
)

app = FastAPI()

@dataclass
class Product:
    id: int
    name: str

DATA = [Product(id=i, name=f"Item {i}") for i in range(1, 101)]

@app.get("/products")
async def get_products(request: Request, pagination: Dict[str, Any] = Depends(get_page_number_pagination)):
    paginator = PageNumberPagination(page_size=10)
    page_items = paginator.paginate_queryset(DATA, request)
    payload = [asdict(p) for p in page_items]
    return paginator.get_paginated_response(payload, total_count=len(DATA), request=request)
```

## CLI commands

See: [`fastjango/cli/main.py`](/fastjango/cli/main.py).

```bash
fastjango-admin --help
fastjango-admin --version
fastjango-admin startproject myproject
fastjango-admin startapp myapp
fastjango-admin runserver --host 0.0.0.0 --port 8000
fastjango-admin makemigrations myapp
fastjango-admin migrate
```

## Notes on the ORM

- The repository includes an experimental ORM layer and SQLAlchemy compatibility utilities.
- APIs are present but still evolving; expect changes and incomplete coverage.
- Relevant modules: [`fastjango/db`](/fastjango/db) · [`fastjango/db/sqlalchemy_compat.py`](/fastjango/db/sqlalchemy_compat.py)

## Built With

- [FastAPI](https://fastapi.tiangolo.com/)
- [Starlette](https://www.starlette.io/)
- [Pydantic](https://docs.pydantic.dev/)
- [Typer](https://typer.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

## License

MIT License. See [`LICENSE`](/LICENSE). 