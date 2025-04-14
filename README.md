# FastJango

FastJango is a web framework inspired by Django that uses FastAPI as its core. 
It provides a familiar Django-like experience with the performance and modern features of FastAPI.

## Features

- Django-like project structure
- FastAPI's high performance
- Type annotations and automatic validation
- Dependency injection
- Automatic API documentation with Swagger and ReDoc
- Familiar Django-like URL patterns
- FastAPI-powered REST API with automatic OpenAPI docs
- Integrated authentication system
- Django-like template system with Jinja2
- ORM support via SQLAlchemy (planned)

pip install typer rich fastapi uvicorn jinja2 python-multipart pydantic

## Installation

```bash
pip install fastjango
```

For development:

```bash
git clone https://github.com/yourusername/fastjango.git
cd fastjango
pip install -e ".[dev]"
```

## Quick Start

### Create a new project

```bash
fastjango-admin startproject myproject
cd myproject
```

### Create a new app

```bash
fastjango-admin startapp myapp
```

Don't forget to add your app to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # FastJango apps
    "myproject.core",
    
    # Your apps
    "myapp",
]
```

### Define models in myapp/models.py

```python
from fastjango.db import models
from fastjango.core.exceptions import ValidationError


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.name
```

### Define routes in myapp/routes.py

```python
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from fastjango.core.dependencies import get_current_user
from .schemas import ItemCreate, ItemRead, ItemUpdate
from .services import ItemService

router = APIRouter(prefix="/items", tags=["items"])
service = ItemService()


@router.get("/", response_model=List[ItemRead])
async def list_items(skip: int = 0, limit: int = 100):
    return await service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, current_user = Depends(get_current_user)):
    return await service.create(item)
```

### Run the development server

```bash
fastjango-admin runserver
```

Or using the manage.py script:

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/docs to see the automatic API documentation.

## Project Structure

When you create a new project, FastJango will generate the following structure:

```
myproject/
├── myproject/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
└── manage.py
```

When you create a new app, FastJango will generate:

```
myapp/
├── __init__.py
├── models.py
├── routes.py
├── schemas.py
├── services.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    └── test_routes.py
```

## Built With

* [FastAPI](https://fastapi.tiangolo.com/) - Web framework
* [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
* [Typer](https://typer.tiangolo.com/) - CLI commands
* [SQLAlchemy](https://www.sqlalchemy.org/) - ORM (planned)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

# Make sure to reinstall after changes
pip install -e .

# Then start your project
./fastjango-admin.py startproject myproject
cd myproject
./fastjango-admin.py runserver 