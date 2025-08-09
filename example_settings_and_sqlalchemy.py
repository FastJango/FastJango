#!/usr/bin/env python3
"""
Example demonstrating Django-like settings and SQLAlchemy models in FastJango.

This example shows how to:
1. Configure database settings like Django
2. Use SQLAlchemy models directly in FastJango apps
3. Use migration commands
"""

import os
import sys
from pathlib import Path

# Add the fastjango package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Set up environment for FastJango
os.environ.setdefault('FASTJANGO_SETTINGS_MODULE', 'example_settings')

# Example settings.py (Django-like configuration)
example_settings_content = '''
"""
Example settings for FastJango project.
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "fastjango-development-key-change-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    "myapp",
]

# Database configuration (Django-like)
DATABASES = {
    "default": {
        "ENGINE": "sqlite",
        "NAME": BASE_DIR / "db.sqlite3",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "engine_options": {
                "echo": True,  # Log SQL queries
            }
        }
    },
    "postgres": {
        "ENGINE": "postgresql",
        "NAME": "myapp",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
        "OPTIONS": {
            "engine_options": {
                "pool_size": 10,
                "max_overflow": 20,
            }
        }
    },
    "mysql": {
        "ENGINE": "mysql",
        "NAME": "myapp",
        "USER": "root",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {
            "engine_options": {
                "pool_size": 10,
                "max_overflow": 20,
            }
        }
    }
}

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
'''

# Create example settings file
with open('example_settings.py', 'w') as f:
    f.write(example_settings_content)

# Example app with SQLAlchemy models
myapp_models_content = '''
"""
Example models using SQLAlchemy directly in FastJango app.
"""

from fastjango.db import (
    SQLAlchemyModel, CharField, TextField, IntegerField, 
    DateTimeField, BooleanField, ForeignKey, relationship
)
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship as SARelationship
from datetime import datetime


# Method 1: Using FastJango SQLAlchemy compatibility
class User(SQLAlchemyModel):
    """User model using FastJango SQLAlchemy compatibility."""
    
    __tablename__ = 'users'
    
    username = CharField(max_length=150, unique=True)
    email = CharField(max_length=254, unique=True)
    first_name = CharField(max_length=30, nullable=True)
    last_name = CharField(max_length=30, nullable=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(default=datetime.now)
    
    def get_full_name(self):
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class Category(SQLAlchemyModel):
    """Category model."""
    
    __tablename__ = 'categories'
    
    name = CharField(max_length=100)
    slug = CharField(max_length=100, unique=True)
    description = TextField(nullable=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now, onupdate=datetime.now)


class Product(SQLAlchemyModel):
    """Product model with relationships."""
    
    __tablename__ = 'products'
    
    name = CharField(max_length=200)
    slug = CharField(max_length=200, unique=True)
    description = TextField(nullable=True)
    price = Column(Integer)  # Direct SQLAlchemy column
    stock = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    category_id = ForeignKey('categories.id')
    created_by_id = ForeignKey('users.id', nullable=True)
    
    # SQLAlchemy relationships
    category = SARelationship("Category", backref="products")
    created_by = SARelationship("User", backref="created_products")


# Method 2: Using pure SQLAlchemy with FastJango compatibility
class Order(SQLAlchemyModel):
    """Order model using pure SQLAlchemy columns."""
    
    __tablename__ = 'orders'
    
    # Pure SQLAlchemy columns
    order_number = Column(String(20), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_amount = Column(Integer, nullable=False)
    status = Column(String(20), default='pending')
    order_date = Column(DateTime, default=datetime.now)
    shipping_address = Column(Text, nullable=False)
    
    # Relationships
    customer = SARelationship("User", backref="orders")


class OrderItem(SQLAlchemyModel):
    """Order item model."""
    
    __tablename__ = 'order_items'
    
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, nullable=False)
    
    # Relationships
    order = SARelationship("Order", backref="items")
    product = SARelationship("Product", backref="order_items")
'''

# Create example app directory and models
myapp_dir = Path('myapp')
myapp_dir.mkdir(exist_ok=True)

# Create __init__.py
(myapp_dir / '__init__.py').write_text('')

# Create models.py
(myapp_dir / 'models.py').write_text(myapp_models_content)

# Create migrations directory
migrations_dir = myapp_dir / 'migrations'
migrations_dir.mkdir(exist_ok=True)
(migrations_dir / '__init__.py').write_text('')

print("Created example project structure:")
print("- example_settings.py (Django-like settings)")
print("- myapp/models.py (SQLAlchemy models)")
print("- myapp/migrations/ (Migration directory)")


def demonstrate_settings():
    """Demonstrate Django-like settings configuration."""
    print("\n=== Django-like Settings Configuration ===")
    
    # Import settings
    import example_settings
    
    print("Database configurations:")
    for db_name, config in example_settings.DATABASES.items():
        print(f"  {db_name}:")
        print(f"    Engine: {config['ENGINE']}")
        print(f"    Name: {config['NAME']}")
        if config.get('USER'):
            print(f"    User: {config['USER']}")
        if config.get('HOST'):
            print(f"    Host: {config['HOST']}")
        if config.get('PORT'):
            print(f"    Port: {config['PORT']}")
        print()


def demonstrate_sqlalchemy_models():
    """Demonstrate SQLAlchemy models in FastJango."""
    print("\n=== SQLAlchemy Models in FastJango ===")
    
    # Import models
    from myapp.models import User, Category, Product, Order, OrderItem
    
    print("Available models:")
    print(f"  - {User.__name__}: {User.__tablename__}")
    print(f"  - {Category.__name__}: {Category.__tablename__}")
    print(f"  - {Product.__name__}: {Product.__tablename__}")
    print(f"  - {Order.__name__}: {Order.__tablename__}")
    print(f"  - {OrderItem.__name__}: {OrderItem.__tablename__}")
    
    print("\nModel fields:")
    for model_class in [User, Category, Product, Order, OrderItem]:
        print(f"\n{model_class.__name__}:")
        for column in model_class.__table__.columns:
            print(f"  - {column.name}: {column.type}")
    
    print("\nRelationships:")
    for model_class in [Product, Order, OrderItem]:
        print(f"\n{model_class.__name__}:")
        for rel in model_class.__mapper__.relationships:
            print(f"  - {rel.key}: {rel.mapper.class_.__name__}")


def demonstrate_migrations():
    """Demonstrate migration commands."""
    print("\n=== Migration Commands ===")
    
    print("Available commands:")
    print("  fastjango-admin makemigrations myapp")
    print("  fastjango-admin makemigrations myapp --name add_user_model")
    print("  fastjango-admin migrate")
    print("  fastjango-admin migrate myapp")
    print("  fastjango-admin migrate --show")
    print("  fastjango-admin migrate myapp --rollback 20240101_120000_add_user_model")
    
    print("\nOr using manage.py:")
    print("  python manage.py makemigrations myapp")
    print("  python manage.py migrate")
    print("  python manage.py migrate --show")


def demonstrate_model_usage():
    """Demonstrate using the models."""
    print("\n=== Model Usage Examples ===")
    
    from fastjango.db.connection import create_tables
    from myapp.models import User, Category, Product
    
    # Create tables
    create_tables()
    print("Created database tables")
    
    # Create instances
    user = User(
        username="john_doe",
        email="john@example.com",
        first_name="John",
        last_name="Doe"
    )
    user.save()
    print(f"Created user: {user}")
    
    category = Category(
        name="Electronics",
        slug="electronics",
        description="Electronic devices and gadgets"
    )
    category.save()
    print(f"Created category: {category}")
    
    product = Product(
        name="Smartphone",
        slug="smartphone",
        description="Latest smartphone model",
        price=59999,  # In cents
        stock=50,
        category=category,
        created_by=user
    )
    product.save()
    print(f"Created product: {product}")
    
    # Query using Django-like API
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    active_products = Product.objects.filter(is_active=True)
    print(f"Active products: {active_products.count()}")
    
    # Query using SQLAlchemy directly
    from fastjango.db.connection import get_session
    session = get_session()
    
    # Get all categories
    categories = session.query(Category).all()
    print(f"Categories: {[cat.name for cat in categories]}")
    
    # Get products with relationships
    products_with_category = session.query(Product).join(Category).all()
    for product in products_with_category:
        print(f"Product: {product.name} in category: {product.category.name}")


def main():
    """Run the demonstration."""
    print("FastJango Django-like Settings and SQLAlchemy Models Example")
    print("=" * 60)
    
    demonstrate_settings()
    demonstrate_sqlalchemy_models()
    demonstrate_migrations()
    demonstrate_model_usage()
    
    print("\nExample completed successfully!")
    print("\nTo try the migration commands:")
    print("1. fastjango-admin makemigrations myapp")
    print("2. fastjango-admin migrate")
    print("3. fastjango-admin migrate --show")


if __name__ == "__main__":
    main()
