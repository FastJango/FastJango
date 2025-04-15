#!/usr/bin/env python
"""
Tests for FastJango form handling functionality.
"""

import os
import sys
import unittest
from decimal import Decimal
from datetime import date, datetime, time

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango form components
from fastjango.forms import (
    Form,
    CharField,
    BooleanField,
    IntegerField,
    DecimalField,
    EmailField,
    URLField,
    DateField,
    TimeField,
    DateTimeField,
    ChoiceField,
    MultipleChoiceField,
    ValidationError,
)


class ContactForm(Form):
    """Example contact form for testing."""
    
    name = CharField(max_length=100)
    email = EmailField()
    subject = CharField(max_length=200)
    message = CharField(max_length=1000, required=False)
    cc_myself = BooleanField(required=False)


class SignupForm(Form):
    """Example signup form with various fields for testing."""
    
    username = CharField(min_length=3, max_length=30)
    email = EmailField()
    password = CharField(min_length=8)
    confirm_password = CharField()
    age = IntegerField(min_value=18)
    newsletter = BooleanField(required=False)
    website = URLField(required=False)
    birthdate = DateField(required=False)
    preferred_time = TimeField(required=False)
    registration_date = DateTimeField(required=False)
    
    subscription = ChoiceField(choices=[
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
    ])
    
    interests = MultipleChoiceField(choices=[
        ('tech', 'Technology'),
        ('sports', 'Sports'),
        ('music', 'Music'),
        ('travel', 'Travel'),
    ], required=False)
    
    def clean(self):
        """Custom validation for the entire form."""
        cleaned_data = super().clean()
        
        # Check if passwords match
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        return cleaned_data


class SimpleFormTest(unittest.TestCase):
    """Test suite for simple form functionality."""
    
    def test_valid_form(self):
        """Test a valid form."""
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message.",
            "cc_myself": True,
        }
        
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data["name"], "John Doe")
        self.assertEqual(cleaned_data["email"], "john@example.com")
        self.assertEqual(cleaned_data["subject"], "Test Subject")
        self.assertEqual(cleaned_data["message"], "This is a test message.")
        self.assertTrue(cleaned_data["cc_myself"])
    
    def test_invalid_form(self):
        """Test an invalid form."""
        form_data = {
            "name": "John Doe",
            "email": "invalid-email",  # Invalid email
            "subject": "Test Subject",
        }
        
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
    
    def test_required_fields(self):
        """Test required fields."""
        form_data = {
            "name": "John Doe",
            # Missing required email field
            # Missing required subject field
            "message": "This is a test message.",
        }
        
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("subject", form.errors)
    
    def test_optional_fields(self):
        """Test optional fields."""
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            # Optional message field omitted
            # Optional cc_myself field omitted
        }
        
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data.get("message", ""), "")
        self.assertFalse(cleaned_data.get("cc_myself", True))  # Default to False


class FieldValidationTest(unittest.TestCase):
    """Test suite for field validation."""
    
    def test_char_field(self):
        """Test CharField validation."""
        class TestForm(Form):
            name = CharField(min_length=2, max_length=10)
        
        # Valid
        form1 = TestForm(data={"name": "John"})
        self.assertTrue(form1.is_valid())
        
        # Too short
        form2 = TestForm(data={"name": "J"})
        self.assertFalse(form2.is_valid())
        
        # Too long
        form3 = TestForm(data={"name": "John Doe Smith"})
        self.assertFalse(form3.is_valid())
    
    def test_integer_field(self):
        """Test IntegerField validation."""
        class TestForm(Form):
            age = IntegerField(min_value=18, max_value=99)
        
        # Valid
        form1 = TestForm(data={"age": "25"})
        self.assertTrue(form1.is_valid())
        self.assertEqual(form1.cleaned_data["age"], 25)
        
        # Too small
        form2 = TestForm(data={"age": "16"})
        self.assertFalse(form2.is_valid())
        
        # Too large
        form3 = TestForm(data={"age": "100"})
        self.assertFalse(form3.is_valid())
        
        # Not an integer
        form4 = TestForm(data={"age": "twenty"})
        self.assertFalse(form4.is_valid())
    
    def test_decimal_field(self):
        """Test DecimalField validation."""
        class TestForm(Form):
            price = DecimalField(max_digits=5, decimal_places=2)
        
        # Valid
        form1 = TestForm(data={"price": "99.99"})
        self.assertTrue(form1.is_valid())
        self.assertEqual(form1.cleaned_data["price"], Decimal("99.99"))
        
        # Too many digits
        form2 = TestForm(data={"price": "1000.00"})
        self.assertFalse(form2.is_valid())
        
        # Too many decimal places
        form3 = TestForm(data={"price": "99.999"})
        self.assertFalse(form3.is_valid())
        
        # Not a number
        form4 = TestForm(data={"price": "price"})
        self.assertFalse(form4.is_valid())
    
    def test_email_field(self):
        """Test EmailField validation."""
        class TestForm(Form):
            email = EmailField()
        
        # Valid
        form1 = TestForm(data={"email": "test@example.com"})
        self.assertTrue(form1.is_valid())
        
        # Invalid
        form2 = TestForm(data={"email": "invalid-email"})
        self.assertFalse(form2.is_valid())
    
    def test_url_field(self):
        """Test URLField validation."""
        class TestForm(Form):
            website = URLField()
        
        # Valid
        form1 = TestForm(data={"website": "https://example.com"})
        self.assertTrue(form1.is_valid())
        
        # Invalid
        form2 = TestForm(data={"website": "invalid-url"})
        self.assertFalse(form2.is_valid())
    
    def test_date_field(self):
        """Test DateField validation."""
        class TestForm(Form):
            start_date = DateField()
        
        # Valid (YYYY-MM-DD)
        form1 = TestForm(data={"start_date": "2023-05-15"})
        self.assertTrue(form1.is_valid())
        self.assertEqual(form1.cleaned_data["start_date"], date(2023, 5, 15))
        
        # Invalid
        form2 = TestForm(data={"start_date": "not-a-date"})
        self.assertFalse(form2.is_valid())
    
    def test_time_field(self):
        """Test TimeField validation."""
        class TestForm(Form):
            start_time = TimeField()
        
        # Valid (HH:MM:SS)
        form1 = TestForm(data={"start_time": "14:30:00"})
        self.assertTrue(form1.is_valid())
        self.assertEqual(form1.cleaned_data["start_time"], time(14, 30, 0))
        
        # Also valid (HH:MM)
        form2 = TestForm(data={"start_time": "14:30"})
        self.assertTrue(form2.is_valid())
        self.assertEqual(form2.cleaned_data["start_time"], time(14, 30))
        
        # Invalid
        form3 = TestForm(data={"start_time": "not-a-time"})
        self.assertFalse(form3.is_valid())
    
    def test_choice_field(self):
        """Test ChoiceField validation."""
        class TestForm(Form):
            color = ChoiceField(choices=[
                ('red', 'Red'),
                ('green', 'Green'),
                ('blue', 'Blue'),
            ])
        
        # Valid
        form1 = TestForm(data={"color": "red"})
        self.assertTrue(form1.is_valid())
        
        # Invalid (not in choices)
        form2 = TestForm(data={"color": "purple"})
        self.assertFalse(form2.is_valid())
    
    def test_multiple_choice_field(self):
        """Test MultipleChoiceField validation."""
        class TestForm(Form):
            colors = MultipleChoiceField(choices=[
                ('red', 'Red'),
                ('green', 'Green'),
                ('blue', 'Blue'),
            ])
        
        # Valid (single choice)
        form1 = TestForm(data={"colors": ["red"]})
        self.assertTrue(form1.is_valid())
        
        # Valid (multiple choices)
        form2 = TestForm(data={"colors": ["red", "blue"]})
        self.assertTrue(form2.is_valid())
        self.assertEqual(form2.cleaned_data["colors"], ["red", "blue"])
        
        # Invalid (not in choices)
        form3 = TestForm(data={"colors": ["red", "purple"]})
        self.assertFalse(form3.is_valid())


class ComplexFormTest(unittest.TestCase):
    """Test suite for complex form functionality."""
    
    def test_valid_signup_form(self):
        """Test a valid signup form with various fields."""
        form_data = {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "age": "25",
            "newsletter": "true",
            "website": "https://example.com",
            "birthdate": "1990-01-01",
            "preferred_time": "14:30",
            "registration_date": "2023-05-15T14:30:00",
            "subscription": "basic",
            "interests": ["tech", "music"],
        }
        
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data["username"], "johndoe")
        self.assertEqual(cleaned_data["email"], "john@example.com")
        self.assertEqual(cleaned_data["password"], "password123")
        self.assertEqual(cleaned_data["confirm_password"], "password123")
        self.assertEqual(cleaned_data["age"], 25)
        self.assertTrue(cleaned_data["newsletter"])
        self.assertEqual(cleaned_data["website"], "https://example.com")
        self.assertEqual(cleaned_data["birthdate"], date(1990, 1, 1))
        self.assertEqual(cleaned_data["preferred_time"], time(14, 30))
        self.assertEqual(
            cleaned_data["registration_date"],
            datetime(2023, 5, 15, 14, 30, 0)
        )
        self.assertEqual(cleaned_data["subscription"], "basic")
        self.assertEqual(cleaned_data["interests"], ["tech", "music"])
    
    def test_passwords_not_matching(self):
        """Test form with passwords that don't match."""
        form_data = {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "password123",
            "confirm_password": "different",  # Different password
            "age": "25",
            "subscription": "basic",
        }
        
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)  # Form-level error


def run_tests():
    """Run the form tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 