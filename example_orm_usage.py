#!/usr/bin/env python3
"""
Example usage of FastJango ORM.

This example demonstrates how to use the FastJango ORM with SQLAlchemy backend.
"""

import os
import sys
from datetime import datetime

# Add the fastjango package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from fastjango.db import (
    Model, CharField, TextField, IntegerField, DateTimeField, 
    BooleanField, ForeignKey, ManyToManyField, EmailField, URLField,
    DecimalField, DateField, TimeField, UUIDField, SlugField,
    ValidationError
)


# Example User model
class User(Model):
    """Example User model."""
    
    username = CharField(max_length=150, unique=True)
    email = EmailField(max_length=254, unique=True)
    first_name = CharField(max_length=30, blank=True)
    last_name = CharField(max_length=30, blank=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = 'users'
    
    def clean(self):
        """Custom validation."""
        if self.username.lower() in ['admin', 'root', 'system']:
            raise ValidationError({"username": "Username cannot be a reserved name"})
    
    def get_full_name(self):
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


# Example Category model
class Category(Model):
    """Example Category model."""
    
    name = CharField(max_length=100)
    slug = SlugField(max_length=100, unique=True)
    description = TextField(blank=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        table_name = 'categories'
        ordering = ['name']


# Example Product model with relationships
class Product(Model):
    """Example Product model with relationships."""
    
    name = CharField(max_length=200)
    slug = SlugField(max_length=200, unique=True)
    description = TextField(blank=True)
    price = DecimalField(max_digits=10, decimal_places=2)
    stock = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Relationships
    category = ForeignKey(Category, on_delete='CASCADE')
    created_by = ForeignKey(User, on_delete='SET_NULL', null=True)
    
    class Meta:
        table_name = 'products'
        ordering = ['-created_at']


# Example Order model
class Order(Model):
    """Example Order model."""
    
    order_number = CharField(max_length=20, unique=True)
    customer = ForeignKey(User, on_delete='CASCADE')
    total_amount = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(max_length=20, default='pending')
    order_date = DateTimeField(auto_now_add=True)
    shipping_address = TextField()
    
    class Meta:
        table_name = 'orders'


# Example OrderItem model for many-to-many relationship
class OrderItem(Model):
    """Example OrderItem model."""
    
    order = ForeignKey(Order, on_delete='CASCADE')
    product = ForeignKey(Product, on_delete='CASCADE')
    quantity = IntegerField(default=1)
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        table_name = 'order_items'


def create_tables():
    """Create all database tables."""
    from fastjango.db.connection import create_tables
    create_tables()
    print("Created all database tables")


def example_basic_operations():
    """Demonstrate basic model operations."""
    print("\n=== Basic Model Operations ===")
    
    # Create a user
    user = User(
        username="john_doe",
        email="john@example.com",
        first_name="John",
        last_name="Doe"
    )
    user.save()
    print(f"Created user: {user}")
    
    # Create a category
    category = Category(
        name="Electronics",
        slug="electronics",
        description="Electronic devices and gadgets"
    )
    category.save()
    print(f"Created category: {category}")
    
    # Create a product
    product = Product(
        name="Smartphone",
        slug="smartphone",
        description="Latest smartphone model",
        price=599.99,
        stock=50,
        category=category,
        created_by=user
    )
    product.save()
    print(f"Created product: {product}")


def example_queryset_operations():
    """Demonstrate QuerySet operations."""
    print("\n=== QuerySet Operations ===")
    
    # Get all users
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    # Filter users
    active_users = User.objects.filter(is_active=True)
    print(f"Active users: {active_users.count()}")
    
    # Get a specific user
    try:
        user = User.objects.get(username="john_doe")
        print(f"Found user: {user.get_full_name()}")
    except User.DoesNotExist:
        print("User not found")
    
    # Create multiple categories
    categories_data = [
        {"name": "Books", "slug": "books", "description": "Books and literature"},
        {"name": "Clothing", "slug": "clothing", "description": "Fashion and apparel"},
        {"name": "Home & Garden", "slug": "home-garden", "description": "Home improvement"},
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=cat_data["slug"],
            defaults=cat_data
        )
        if created:
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")
    
    # Order by field
    categories = Category.objects.order_by('name')
    print("Categories in alphabetical order:")
    for cat in categories:
        print(f"  - {cat.name}")
    
    # Complex filtering
    expensive_products = Product.objects.filter(
        price__gte=500,
        is_active=True
    ).order_by('-price')
    
    print(f"Expensive products (>= $500): {expensive_products.count()}")
    for product in expensive_products:
        print(f"  - {product.name}: ${product.price}")


def example_validation():
    """Demonstrate model validation."""
    print("\n=== Model Validation ===")
    
    # Try to create a user with invalid email
    try:
        invalid_user = User(
            username="test_user",
            email="invalid-email",
            first_name="Test"
        )
        invalid_user.save()
    except ValidationError as e:
        print(f"Validation error: {e}")
    
    # Try to create a user with reserved username
    try:
        reserved_user = User(
            username="admin",
            email="admin@example.com"
        )
        reserved_user.save()
    except ValidationError as e:
        print(f"Validation error: {e}")


def example_relationships():
    """Demonstrate relationship operations."""
    print("\n=== Relationship Operations ===")
    
    # Get user and create products for them
    user = User.objects.get(username="john_doe")
    category = Category.objects.get(slug="electronics")
    
    # Create products for the user
    products = [
        Product(
            name="Laptop",
            slug="laptop",
            description="High-performance laptop",
            price=1299.99,
            stock=25,
            category=category,
            created_by=user
        ),
        Product(
            name="Tablet",
            slug="tablet",
            description="Portable tablet device",
            price=399.99,
            stock=30,
            category=category,
            created_by=user
        )
    ]
    
    for product in products:
        product.save()
        print(f"Created product: {product.name} by {product.created_by.username}")
    
    # Get products by user
    user_products = Product.objects.filter(created_by=user)
    print(f"Products created by {user.username}: {user_products.count()}")
    
    # Get products by category
    electronics_products = Product.objects.filter(category__slug="electronics")
    print(f"Electronics products: {electronics_products.count()}")


def example_bulk_operations():
    """Demonstrate bulk operations."""
    print("\n=== Bulk Operations ===")
    
    # Bulk create users
    users_data = [
        {"username": "alice", "email": "alice@example.com", "first_name": "Alice"},
        {"username": "bob", "email": "bob@example.com", "first_name": "Bob"},
        {"username": "charlie", "email": "charlie@example.com", "first_name": "Charlie"},
    ]
    
    users = [User(**data) for data in users_data]
    created_users = User.objects.bulk_create(users)
    print(f"Bulk created {len(created_users)} users")
    
    # Bulk update
    updated_count = User.objects.filter(is_active=True).update(is_staff=True)
    print(f"Updated {updated_count} users to staff status")


def example_advanced_queryset():
    """Demonstrate advanced QuerySet operations."""
    print("\n=== Advanced QuerySet Operations ===")
    
    # Values and values_list
    user_emails = User.objects.values_list('email', flat=True)
    print("User emails:", list(user_emails))
    
    # Distinct
    unique_statuses = Order.objects.values_list('status', flat=True).distinct()
    print("Unique order statuses:", list(unique_statuses))
    
    # Exclude
    non_staff_users = User.objects.exclude(is_staff=True)
    print(f"Non-staff users: {non_staff_users.count()}")
    
    # Complex filtering with lookups
    recent_products = Product.objects.filter(
        created_at__gte=datetime(2024, 1, 1),
        price__lt=1000
    ).order_by('-created_at')
    
    print(f"Recent affordable products: {recent_products.count()}")


def main():
    """Run the example."""
    print("FastJango ORM Example")
    print("=" * 50)
    
    # Set up database
    create_tables()
    
    # Run examples
    example_basic_operations()
    example_queryset_operations()
    example_validation()
    example_relationships()
    example_bulk_operations()
    example_advanced_queryset()
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
