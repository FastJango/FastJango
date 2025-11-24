import pytest
from sqlalchemy import Column
from fastjango.db.fields import BinaryField

def test_binary_field_import():
    try:
        # This will fail if Binary is imported from sqlalchemy
        from fastjango.db.fields import BinaryField
        print("Import successful")
    except ImportError as e:
        print(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    test_binary_field_import()
