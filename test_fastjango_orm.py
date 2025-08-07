#!/usr/bin/env python3
"""
Comprehensive test suite for FastJango ORM.

This test suite covers:
- Model creation and field types
- QuerySet operations
- Database migrations
- SQLAlchemy compatibility
- Model validation
- Database transactions
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, date, time
from decimal import Decimal
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_environment():
    """Set up test environment with temporary database and settings."""
    
    # Create temporary directory for test database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Test settings
    test_settings = {
        'DATABASES': {
            'default': {
                'ENGINE': 'fastjango.db.backends.sqlite3',
                'NAME': db_path,
                'OPTIONS': {
                    'timeout': 20,
                }
            }
        },
        'INSTALLED_APPS': ['testapp'],
        'BASE_DIR': Path(__file__).parent,
        'MEDIA_ROOT': os.path.join(temp_dir, 'media'),
        'MEDIA_URL': '/media/',
        'STATIC_ROOT': os.path.join(temp_dir, 'static'),
        'STATIC_URL': '/static/',
    }
    
    # Set environment variable for settings
    os.environ['FASTJANGO_SETTINGS_MODULE'] = 'test_settings'
    
    # Create test settings module
    with open('test_settings.py', 'w') as f:
        f.write(f"""
# Test settings for FastJango ORM
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

DATABASES = {{
    'default': {{
        'ENGINE': 'fastjango.db.backends.sqlite3',
        'NAME': '{db_path}',
        'OPTIONS': {{
            'timeout': 20,
        }}
    }}
}}

INSTALLED_APPS = ['testapp']

MEDIA_ROOT = '{test_settings["MEDIA_ROOT"]}'
MEDIA_URL = '/media/'
STATIC_ROOT = '{test_settings["STATIC_ROOT"]}'
STATIC_URL = '/static/'
""")
    
    return temp_dir, db_path, test_settings


def cleanup_test_environment(temp_dir):
    """Clean up test environment."""
    try:
        shutil.rmtree(temp_dir)
        if os.path.exists('test_settings.py'):
            os.remove('test_settings.py')
    except Exception as e:
        print(f"Warning: Could not clean up test environment: {e}")


def test_imports():
    """Test that all ORM components can be imported."""
    print("Testing imports...")
    
    try:
        from fastjango.db import models, fields, QuerySet
        from fastjango.db.models import Model, Manager
        from fastjango.db.fields import (
            CharField, TextField, IntegerField, FloatField, DecimalField,
            BooleanField, DateField, DateTimeField, TimeField, EmailField,
            URLField, FileField, ImageField, ForeignKey, ManyToManyField
        )
        from fastjango.db.connection import get_engine, get_session, close_connections
        from fastjango.db.migrations import Migration, MigrationOperation
        from fastjango.db.sqlalchemy_compat import SQLAlchemyModel, SQLAlchemyField
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_model_creation():
    """Test basic model creation and field types."""
    print("\nTesting basic model creation...")
    
    try:
        from fastjango.db import models
        from fastjango.db.fields import (
            CharField, TextField, IntegerField, BooleanField, 
            DateField, DateTimeField, EmailField, URLField
        )
        
        class TestUser(models.Model):
            username = CharField(max_length=100, unique=True)
            email = EmailField(max_length=255)
            bio = TextField(blank=True, null=True)
            age = IntegerField(default=0)
            is_active = BooleanField(default=True)
            birth_date = DateField(null=True, blank=True)
            created_at = DateTimeField(auto_now_add=True)
            website = URLField(max_length=200, blank=True, null=True)
            
            class Meta:
                app_label = 'testapp'
                db_table = 'test_users'
        
        # Test model attributes
        assert hasattr(TestUser, 'objects'), "Model should have objects manager"
        assert TestUser._meta.app_label == 'testapp', "App label should be set"
        assert TestUser._meta.db_table == 'test_users', "Table name should be set"
        
        # Test field attributes
        assert TestUser.username.max_length == 100, "CharField max_length should be set"
        assert TestUser.email.max_length == 255, "EmailField max_length should be set"
        assert TestUser.age.default == 0, "IntegerField default should be set"
        assert TestUser.is_active.default is True, "BooleanField default should be set"
        
        print("✅ Basic model creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Basic model creation failed: {e}")
        return False


def test_model_operations():
    """Test model operations like save, delete, and queries."""
    print("\nTesting model operations...")
    
    try:
        from fastjango.db import models
        from fastjango.db.connection import get_session, close_connections
        
        class TestProduct(models.Model):
            name = models.CharField(max_length=200)
            price = models.DecimalField(max_digits=10, decimal_places=2)
            description = models.TextField(blank=True)
            is_available = models.BooleanField(default=True)
            created_at = models.DateTimeField(auto_now_add=True)
            
            class Meta:
                app_label = 'testapp'
        
        # Test model creation
        product = TestProduct(
            name="Test Product",
            price=Decimal("29.99"),
            description="A test product",
            is_available=True
        )
        
        # Test save operation
        product.save()
        assert product.pk is not None, "Model should have primary key after save"
        assert product.id == product.pk, "pk and id should be the same"
        
        # Test QuerySet operations
        products = TestProduct.objects.all()
        assert len(products) == 1, "Should have one product"
        
        # Test filter operation
        available_products = TestProduct.objects.filter(is_available=True)
        assert len(available_products) == 1, "Should have one available product"
        
        # Test get operation
        retrieved_product = TestProduct.objects.get(name="Test Product")
        assert retrieved_product.name == "Test Product", "Should retrieve correct product"
        
        # Test update operation
        TestProduct.objects.filter(name="Test Product").update(price=Decimal("39.99"))
        updated_product = TestProduct.objects.get(name="Test Product")
        assert updated_product.price == Decimal("39.99"), "Price should be updated"
        
        # Test delete operation
        product.delete()
        products_after_delete = TestProduct.objects.all()
        assert len(products_after_delete) == 0, "Product should be deleted"
        
        print("✅ Model operations successful")
        return True
        
    except Exception as e:
        print(f"❌ Model operations failed: {e}")
        return False


def test_queryset_operations():
    """Test QuerySet operations like filter, exclude, order_by, etc."""
    print("\nTesting QuerySet operations...")
    
    try:
        from fastjango.db import models
        from decimal import Decimal
        
        class TestItem(models.Model):
            name = models.CharField(max_length=100)
            category = models.CharField(max_length=50)
            price = models.DecimalField(max_digits=10, decimal_places=2)
            rating = models.IntegerField(default=0)
            is_featured = models.BooleanField(default=False)
            
            class Meta:
                app_label = 'testapp'
        
        # Create test data
        items_data = [
            {"name": "Item 1", "category": "Electronics", "price": Decimal("100.00"), "rating": 5, "is_featured": True},
            {"name": "Item 2", "category": "Books", "price": Decimal("25.00"), "rating": 4, "is_featured": False},
            {"name": "Item 3", "category": "Electronics", "price": Decimal("150.00"), "rating": 3, "is_featured": True},
            {"name": "Item 4", "category": "Clothing", "price": Decimal("50.00"), "rating": 5, "is_featured": False},
        ]
        
        for item_data in items_data:
            item = TestItem(**item_data)
            item.save()
        
        # Test filter
        electronics = TestItem.objects.filter(category="Electronics")
        assert len(electronics) == 2, "Should have 2 electronics items"
        
        # Test exclude
        non_featured = TestItem.objects.exclude(is_featured=True)
        assert len(non_featured) == 2, "Should have 2 non-featured items"
        
        # Test order_by
        by_price = TestItem.objects.order_by('price')
        assert by_price[0].price == Decimal("25.00"), "First item should have lowest price"
        
        # Test reverse order
        by_price_desc = TestItem.objects.order_by('-price')
        assert by_price_desc[0].price == Decimal("150.00"), "First item should have highest price"
        
        # Test multiple filters
        featured_electronics = TestItem.objects.filter(category="Electronics", is_featured=True)
        assert len(featured_electronics) == 1, "Should have 1 featured electronics item"
        
        # Test complex queries
        high_rated = TestItem.objects.filter(rating__gte=4)
        assert len(high_rated) == 2, "Should have 2 high-rated items"
        
        # Test count
        total_count = TestItem.objects.count()
        assert total_count == 4, "Should have 4 total items"
        
        # Test exists
        has_electronics = TestItem.objects.filter(category="Electronics").exists()
        assert has_electronics is True, "Should have electronics items"
        
        # Test first and last
        first_item = TestItem.objects.first()
        last_item = TestItem.objects.last()
        assert first_item is not None, "Should have first item"
        assert last_item is not None, "Should have last item"
        
        print("✅ QuerySet operations successful")
        return True
        
    except Exception as e:
        print(f"❌ QuerySet operations failed: {e}")
        return False


def test_relationships():
    """Test foreign key and many-to-many relationships."""
    print("\nTesting relationships...")
    
    try:
        from fastjango.db import models
        
        class Category(models.Model):
            name = models.CharField(max_length=100, unique=True)
            description = models.TextField(blank=True)
            
            class Meta:
                app_label = 'testapp'
        
        class Product(models.Model):
            name = models.CharField(max_length=200)
            category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
            price = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'testapp'
        
        class Tag(models.Model):
            name = models.CharField(max_length=50, unique=True)
            
            class Meta:
                app_label = 'testapp'
        
        class Article(models.Model):
            title = models.CharField(max_length=200)
            content = models.TextField()
            tags = models.ManyToManyField(Tag, related_name='articles')
            
            class Meta:
                app_label = 'testapp'
        
        # Create test data
        electronics = Category.objects.create(name="Electronics", description="Electronic devices")
        books = Category.objects.create(name="Books", description="Books and publications")
        
        product1 = Product.objects.create(name="Laptop", category=electronics, price=Decimal("999.99"))
        product2 = Product.objects.create(name="Python Book", category=books, price=Decimal("49.99"))
        
        tag1 = Tag.objects.create(name="Technology")
        tag2 = Tag.objects.create(name="Programming")
        tag3 = Tag.objects.create(name="Education")
        
        article1 = Article.objects.create(title="Python Programming", content="Learn Python...")
        article1.tags.add(tag1, tag2)
        
        article2 = Article.objects.create(title="Web Development", content="Build web apps...")
        article2.tags.add(tag1, tag3)
        
        # Test foreign key relationships
        assert product1.category == electronics, "Product should have correct category"
        assert electronics.products.count() == 1, "Category should have one product"
        assert electronics.products.first() == product1, "Category should have correct product"
        
        # Test many-to-many relationships
        assert article1.tags.count() == 2, "Article should have 2 tags"
        assert tag1.articles.count() == 2, "Tag should have 2 articles"
        
        # Test reverse relationships
        electronics_products = electronics.products.all()
        assert len(electronics_products) == 1, "Should have one electronics product"
        
        technology_articles = tag1.articles.all()
        assert len(technology_articles) == 2, "Should have 2 technology articles"
        
        print("✅ Relationships successful")
        return True
        
    except Exception as e:
        print(f"❌ Relationships failed: {e}")
        return False


def test_migrations():
    """Test migration system."""
    print("\nTesting migrations...")
    
    try:
        from fastjango.cli.commands.makemigrations import make_migrations
        from fastjango.cli.commands.migrate import migrate
        
        # Test migration creation
        migration_file = make_migrations('testapp')
        assert migration_file is not None, "Should create migration file"
        assert os.path.exists(migration_file), "Migration file should exist"
        
        # Test migration application
        applied_count = migrate('testapp')
        assert applied_count > 0, "Should apply migrations"
        
        # Test migration status
        from fastjango.db.migrations import MigrationRecorder
        recorder = MigrationRecorder()
        applied_migrations = recorder.get_applied_migrations()
        assert len(applied_migrations) > 0, "Should have applied migrations"
        
        print("✅ Migrations successful")
        return True
        
    except Exception as e:
        print(f"❌ Migrations failed: {e}")
        return False


def test_sqlalchemy_compatibility():
    """Test SQLAlchemy compatibility layer."""
    print("\nTesting SQLAlchemy compatibility...")
    
    try:
        from fastjango.db.sqlalchemy_compat import SQLAlchemyModel, SQLAlchemyField
        from sqlalchemy import Column, String, Integer, Boolean, DateTime
        from sqlalchemy.ext.declarative import declarative_base
        from fastjango.db.connection import get_session
        
        # Create SQLAlchemy model
        Base = declarative_base()
        
        class SQLAlchemyUser(Base, SQLAlchemyModel):
            __tablename__ = 'sqlalchemy_users'
            
            id = Column(Integer, primary_key=True)
            username = Column(String(100), unique=True)
            email = Column(String(255))
            is_active = Column(Boolean, default=True)
            created_at = Column(DateTime, default=datetime.now)
            
            class Meta:
                app_label = 'testapp'
        
        # Test model creation
        user = SQLAlchemyUser(
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        # Test save operation
        session = get_session()
        session.add(user)
        session.commit()
        
        # Test QuerySet operations
        users = SQLAlchemyUser.objects().all()
        assert len(users) == 1, "Should have one user"
        
        # Test filter operation
        active_users = SQLAlchemyUser.objects().filter(is_active=True)
        assert len(active_users) == 1, "Should have one active user"
        
        # Test get operation
        retrieved_user = SQLAlchemyUser.objects().get(username="testuser")
        assert retrieved_user.username == "testuser", "Should retrieve correct user"
        
        print("✅ SQLAlchemy compatibility successful")
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy compatibility failed: {e}")
        return False


def test_model_validation():
    """Test model validation and field validation."""
    print("\nTesting model validation...")
    
    try:
        from fastjango.db import models
        from fastjango.core.exceptions import ValidationError
        
        class ValidatedModel(models.Model):
            name = models.CharField(max_length=50)
            email = models.EmailField()
            age = models.IntegerField(min_value=0, max_value=150)
            score = models.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100)
            
            class Meta:
                app_label = 'testapp'
        
        # Test valid data
        valid_model = ValidatedModel(
            name="Test User",
            email="test@example.com",
            age=25,
            score=Decimal("85.5")
        )
        
        # Test full_clean
        valid_model.full_clean()
        assert valid_model.is_valid(), "Valid model should pass validation"
        
        # Test invalid email
        invalid_email_model = ValidatedModel(
            name="Test User",
            email="invalid-email",
            age=25,
            score=Decimal("85.5")
        )
        
        try:
            invalid_email_model.full_clean()
            assert False, "Should raise validation error for invalid email"
        except ValidationError:
            pass  # Expected
        
        # Test invalid age
        invalid_age_model = ValidatedModel(
            name="Test User",
            email="test@example.com",
            age=200,  # Too high
            score=Decimal("85.5")
        )
        
        try:
            invalid_age_model.full_clean()
            assert False, "Should raise validation error for invalid age"
        except ValidationError:
            pass  # Expected
        
        # Test invalid score
        invalid_score_model = ValidatedModel(
            name="Test User",
            email="test@example.com",
            age=25,
            score=Decimal("150.0")  # Too high
        )
        
        try:
            invalid_score_model.full_clean()
            assert False, "Should raise validation error for invalid score"
        except ValidationError:
            pass  # Expected
        
        print("✅ Model validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False


def test_database_transactions():
    """Test database transactions."""
    print("\nTesting database transactions...")
    
    try:
        from fastjango.db import models
        from fastjango.db.connection import session_scope
        
        class TransactionTest(models.Model):
            name = models.CharField(max_length=100)
            value = models.IntegerField()
            
            class Meta:
                app_label = 'testapp'
        
        # Test successful transaction
        with session_scope() as session:
            model1 = TransactionTest(name="Test 1", value=100)
            model2 = TransactionTest(name="Test 2", value=200)
            session.add(model1)
            session.add(model2)
            # Transaction should commit automatically
        
        # Verify data was saved
        saved_models = TransactionTest.objects.all()
        assert len(saved_models) == 2, "Should have 2 saved models"
        
        # Test rollback on exception
        try:
            with session_scope() as session:
                model3 = TransactionTest(name="Test 3", value=300)
                session.add(model3)
                raise Exception("Simulated error")
        except Exception:
            pass  # Expected
        
        # Verify rollback occurred
        models_after_rollback = TransactionTest.objects.all()
        assert len(models_after_rollback) == 2, "Should still have only 2 models after rollback"
        
        print("✅ Database transactions successful")
        return True
        
    except Exception as e:
        print(f"❌ Database transactions failed: {e}")
        return False


def run_all_tests():
    """Run all test cases."""
    print("🚀 Starting FastJango ORM Test Suite")
    print("=" * 50)
    
    # Set up test environment
    temp_dir, db_path, test_settings = setup_test_environment()
    
    try:
        # Run all tests
        tests = [
            test_imports,
            test_basic_model_creation,
            test_model_operations,
            test_queryset_operations,
            test_relationships,
            test_migrations,
            test_sqlalchemy_compatibility,
            test_model_validation,
            test_database_transactions,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! FastJango ORM is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
            return False
            
    finally:
        # Clean up test environment
        cleanup_test_environment(temp_dir)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)