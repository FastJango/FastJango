#!/usr/bin/env python3
"""
Test script to verify migrations work with SQLAlchemy compatibility.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the fastjango package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Set up environment
os.environ.setdefault('FASTJANGO_SETTINGS_MODULE', 'test_settings')

# Create test settings
test_settings_content = '''
"""
Test settings for migration testing.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    "default": {
        "ENGINE": "sqlite",
        "NAME": BASE_DIR / "test_db.sqlite3",
        "OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "engine_options": {"echo": True}
        }
    }
}

INSTALLED_APPS = [
    "testapp",
]
'''

# Create test settings file
with open('test_settings.py', 'w') as f:
    f.write(test_settings_content)

# Create test app with SQLAlchemy models
testapp_models_content = '''
"""
Test models using SQLAlchemy compatibility.
"""

from fastjango.db import (
    SQLAlchemyModel, CharField, TextField, IntegerField, 
    DateTimeField, BooleanField, ForeignKey, relationship
)
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship as SARelationship
from datetime import datetime


class TestUser(SQLAlchemyModel):
    """Test user model using SQLAlchemy compatibility."""
    
    __tablename__ = 'test_users'
    
    username = CharField(max_length=150, unique=True)
    email = CharField(max_length=254, unique=True)
    first_name = CharField(max_length=30, nullable=True)
    last_name = CharField(max_length=30, nullable=True)
    is_active = BooleanField(default=True)
    date_joined = DateTimeField(default=datetime.now)


class TestCategory(SQLAlchemyModel):
    """Test category model."""
    
    __tablename__ = 'test_categories'
    
    name = CharField(max_length=100)
    slug = CharField(max_length=100, unique=True)
    description = TextField(nullable=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)


class TestProduct(SQLAlchemyModel):
    """Test product model with relationships."""
    
    __tablename__ = 'test_products'
    
    name = CharField(max_length=200)
    slug = CharField(max_length=200, unique=True)
    description = TextField(nullable=True)
    price = Column(Integer)  # Direct SQLAlchemy column
    stock = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    
    # Relationships
    category_id = ForeignKey('test_categories.id')
    created_by_id = ForeignKey('test_users.id', nullable=True)
    
    # SQLAlchemy relationships
    category = SARelationship("TestCategory", backref="products")
    created_by = SARelationship("TestUser", backref="created_products")


class TestOrder(SQLAlchemyModel):
    """Test order model using pure SQLAlchemy columns."""
    
    __tablename__ = 'test_orders'
    
    # Pure SQLAlchemy columns
    order_number = Column(String(20), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('test_users.id'), nullable=False)
    total_amount = Column(Integer, nullable=False)
    status = Column(String(20), default='pending')
    order_date = Column(DateTime, default=datetime.now)
    
    # Relationships
    customer = SARelationship("TestUser", backref="orders")
'''

# Create test app directory
testapp_dir = Path('testapp')
testapp_dir.mkdir(exist_ok=True)

# Create __init__.py
(testapp_dir / '__init__.py').write_text('')

# Create models.py
(testapp_dir / 'models.py').write_text(testapp_models_content)

# Create migrations directory
migrations_dir = testapp_dir / 'migrations'
migrations_dir.mkdir(exist_ok=True)
(migrations_dir / '__init__.py').write_text('')

print("Created test project structure:")
print("- test_settings.py")
print("- testapp/models.py (SQLAlchemy models)")
print("- testapp/migrations/")


def test_migration_detection():
    """Test if migrations can detect SQLAlchemy models."""
    print("\n=== Testing Migration Detection ===")
    
    try:
        from fastjango.cli.commands.makemigrations import detect_model_changes
        
        # Test model change detection
        operations = detect_model_changes('testapp', testapp_dir)
        
        print(f"Detected {len(operations)} migration operations:")
        for i, operation in enumerate(operations, 1):
            print(f"  {i}. {operation.describe()}")
        
        return len(operations) > 0
        
    except Exception as e:
        print(f"Error detecting model changes: {e}")
        return False


def test_migration_creation():
    """Test if migrations can be created for SQLAlchemy models."""
    print("\n=== Testing Migration Creation ===")
    
    try:
        from fastjango.cli.commands.makemigrations import make_migrations
        
        # Create migration
        migration_file = make_migrations('testapp', 'test_sqlalchemy_models')
        
        if migration_file:
            print(f"Created migration file: {migration_file}")
            
            # Read and display migration content
            content = migration_file.read_text()
            print("\nMigration content:")
            print("=" * 50)
            print(content)
            print("=" * 50)
            
            return True
        else:
            print("No migration created (no changes detected)")
            return False
            
    except Exception as e:
        print(f"Error creating migration: {e}")
        return False


def test_migration_application():
    """Test if migrations can be applied to database."""
    print("\n=== Testing Migration Application ===")
    
    try:
        from fastjango.cli.commands.migrate import migrate_app
        from fastjango.db.connection import get_engine, create_tables
        
        # Create tables first (for initial setup)
        create_tables()
        print("Created initial database tables")
        
        # Apply migrations
        applied_count = migrate_app('testapp', fake=False)
        print(f"Applied {applied_count} migrations")
        
        # Check if tables exist
        engine = get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['test_users', 'test_categories', 'test_products', 'test_orders']
        found_tables = [table for table in tables if table in expected_tables]
        
        print(f"Found tables: {found_tables}")
        print(f"Expected tables: {expected_tables}")
        
        return len(found_tables) == len(expected_tables)
        
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return False


def test_model_usage():
    """Test if SQLAlchemy models work after migrations."""
    print("\n=== Testing Model Usage ===")
    
    try:
        from testapp.models import TestUser, TestCategory, TestProduct
        from fastjango.db.connection import get_session
        
        # Create test data
        session = get_session()
        
        # Create user
        user = TestUser(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        session.commit()
        print(f"Created user: {user}")
        
        # Create category
        category = TestCategory(
            name="Test Category",
            slug="test-category",
            description="Test category description"
        )
        session.add(category)
        session.commit()
        print(f"Created category: {category}")
        
        # Create product
        product = TestProduct(
            name="Test Product",
            slug="test-product",
            description="Test product description",
            price=1000,
            stock=10,
            category=category,
            created_by=user
        )
        session.add(product)
        session.commit()
        print(f"Created product: {product}")
        
        # Test QuerySet operations
        users = TestUser.objects.all()
        print(f"Total users: {users.count()}")
        
        active_products = TestProduct.objects.filter(is_active=True)
        print(f"Active products: {active_products.count()}")
        
        # Test SQLAlchemy queries
        all_categories = session.query(TestCategory).all()
        print(f"Categories: {[cat.name for cat in all_categories]}")
        
        products_with_category = session.query(TestProduct).join(TestCategory).all()
        for product in products_with_category:
            print(f"Product: {product.name} in category: {product.category.name}")
        
        return True
        
    except Exception as e:
        print(f"Error testing model usage: {e}")
        return False


def test_migration_rollback():
    """Test if migrations can be rolled back."""
    print("\n=== Testing Migration Rollback ===")
    
    try:
        from fastjango.cli.commands.migrate import rollback_migration
        from fastjango.db.migrations import MigrationRecorder
        from fastjango.db.connection import get_engine
        
        # Get applied migrations
        engine = get_engine()
        recorder = MigrationRecorder(engine)
        applied = recorder.get_applied_migrations()
        
        print(f"Applied migrations: {applied}")
        
        if applied:
            # Try to rollback the first migration
            first_migration = applied[0]
            success = rollback_migration(
                first_migration['app_label'], 
                first_migration['name']
            )
            print(f"Rollback success: {success}")
            return success
        else:
            print("No applied migrations to rollback")
            return True
            
    except Exception as e:
        print(f"Error testing rollback: {e}")
        return False


def cleanup():
    """Clean up test files."""
    print("\n=== Cleaning Up ===")
    
    files_to_remove = [
        'test_settings.py',
        'test_db.sqlite3',
        'testapp',
    ]
    
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"Removed: {file_path}")


def main():
    """Run all tests."""
    print("Testing SQLAlchemy Migration Compatibility")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Migration Detection", test_migration_detection()))
    results.append(("Migration Creation", test_migration_creation()))
    results.append(("Migration Application", test_migration_application()))
    results.append(("Model Usage", test_model_usage()))
    results.append(("Migration Rollback", test_migration_rollback()))
    
    # Report results
    print("\n=== Test Results ===")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! SQLAlchemy migrations work correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    # Cleanup
    cleanup()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)