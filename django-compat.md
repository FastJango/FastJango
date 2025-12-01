# Django Compatibility Layer

This document details the architectural decisions and compatibility layers implemented in FastJango to bridge Django patterns with SQLAlchemy and FastAPI.

## Overview

FastJango aims to provide a familiar Django-like experience while leveraging modern Python features, FastAPI, and SQLAlchemy. Key challenges involve mapping Django's "active record" style (rich models with field descriptors) to SQLAlchemy's declarative style (instrumented attributes) and handling session management in an async environment.

## 1. ORM Architecture (`fastjango.db.models`)

### Model Metaclass (`ModelMeta`)
Django models rely heavily on a custom metaclass to process field definitions. FastJango implements `ModelMeta` which inherits from SQLAlchemy's `DeclarativeMeta`.

*   **Field Mapping:** Iterates over `FastJango` field definitions (e.g., `CharField`, `ForeignKey`) and replaces them with SQLAlchemy `Column` objects or `relationship` properties on the class.
*   **Metadata Proxy:** Copies field attributes (e.g., `max_length`, `null`, `default`) from the original `Field` object to the SQLAlchemy `InstrumentedAttribute`. This allows Django-style introspection like `MyModel.my_field.max_length`.
*   **Table Creation:** Automatically generates `__tablename__` based on model name or `Meta.db_table`, and creates association tables for `ManyToManyField`.

### Base Model (`Model`)
*   **Initialization:** `Model.__init__` handles loose initialization (accepting kwargs). It performs type conversion using `field.to_python()` but defers validation to `full_clean()` or `save()`, matching Django's behavior.
*   **Validation:** `full_clean()` calls `validate()` on each field. `save()` automatically calls `full_clean()`.
*   **QuerySet Access:** Provides `objects` manager which returns a `QuerySet`.

## 2. Fields (`fastjango.db.fields`)

FastJango fields wrap SQLAlchemy columns and provide Django-specific logic.

*   **Type Conversion:** `to_python()` converts raw input (e.g., strings from JSON) to Python objects (e.g., `datetime`, `UUID`).
*   **Validation:** `validate()` enforces constraints like `min_value`, `max_value`, regex patterns.
*   **Relationships:**
    *   **ForeignKey:** Automatically renames the column to `{field_name}_id` and creates a `relationship` property with the original name. Configures `backref` with `RelatedManager`.
    *   **ManyToManyField:** Automatically creates an association table and configures `secondary` relationship.

## 3. QuerySet (`fastjango.db.queryset`)

*   **Laziness:** `QuerySet` is lazy. `all()`, `filter()`, `exclude()`, `order_by()` return a cloned `QuerySet`. The query is only executed when iterating, slicing (with step), checking length, or calling `first()`/`get()`.
*   **API:** Mimics Django's API (`filter(field__lookup=value)`, `exclude`, `get`, `create`, `count`, `exists`).
*   **Implementation:** underlyingly constructs a SQLAlchemy `select()` query.

## 4. Session Management (`fastjango.db.connection`)

*   **Scoped Session:** Uses SQLAlchemy's `scoped_session`.
*   **Context Awareness:** Implements a custom scope function (`get_session_scope`) that uses `asyncio.current_task()` in async contexts and `threading.get_ident()` in sync contexts. This ensures thread-safety and async-safety.
*   **Persistence:** Sessions are kept open during a logical scope (request or task) to prevent `DetachedInstanceError` when accessing lazy-loaded attributes.

## 5. Migrations

*   **Detection:** `makemigrations` detects changes by comparing model definitions (including `SQLAlchemyModel` subclasses) against existing database schema.
*   **Serialization:** Properly serializes default values (handling strings and basic types) for migration files.
*   **Loader:** `migrate` command correctly resolves migration file paths regardless of the current working directory.

## 6. Known Differences

*   **Async vs Sync:** While FastJango supports async views, the ORM core currently runs synchronously (blocking) within those views unless run in a threadpool. Future work includes integrating `AsyncSession`.
*   **Validators:** Django validators are functions; FastJango currently embeds common validation logic in Field classes, though `validators` list support is planned.
