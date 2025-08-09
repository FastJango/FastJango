"""
Database connection management for FastJango ORM.
"""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool

from fastjango.core.logging import Logger

logger = Logger("fastjango.db.connection")

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_session: Optional[Session] = None


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from settings.
    
    Returns:
        Database configuration dictionary
    """
    try:
        # Try to import FastJango settings
        import os
        settings_module = os.environ.get('FASTJANGO_SETTINGS_MODULE')
        if settings_module:
            settings = importlib.import_module(settings_module)
            return getattr(settings, 'DATABASES', {}).get('default', {})
    except ImportError:
        pass
    
    # Fallback configuration
    return {
        'ENGINE': 'sqlite',
        'NAME': 'db.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {},
    }


def get_engine() -> Engine:
    """
    Get or create the database engine.
    
    Returns:
        SQLAlchemy engine
    """
    global _engine
    
    if _engine is None:
        config = get_database_config()
        
        # Parse engine type
        engine_type = config.get('ENGINE', 'sqlite')
        options = config.get('OPTIONS', {})
        
        if 'sqlite' in engine_type:
            database_url = f"sqlite:///{config.get('NAME', 'db.sqlite3')}"
            connect_args = {"check_same_thread": False}
            connect_args.update(options.get('connect_args', {}))
            
            _engine = create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
                **options.get('engine_options', {})
            )
        elif 'postgresql' in engine_type or 'postgres' in engine_type:
            user = config.get('USER', '')
            password = config.get('PASSWORD', '')
            host = config.get('HOST', 'localhost')
            port = config.get('PORT', '5432')
            name = config.get('NAME', '')
            
            if user and password:
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
            else:
                database_url = f"postgresql://{host}:{port}/{name}"
            
            _engine = create_engine(database_url, **options.get('engine_options', {}))
        elif 'mysql' in engine_type:
            user = config.get('USER', '')
            password = config.get('PASSWORD', '')
            host = config.get('HOST', 'localhost')
            port = config.get('PORT', '3306')
            name = config.get('NAME', '')
            
            if user and password:
                database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
            else:
                database_url = f"mysql+pymysql://{host}:{port}/{name}"
            
            _engine = create_engine(database_url, **options.get('engine_options', {}))
        else:
            raise ValueError(f"Unsupported database engine: {engine_type}")
        
        logger.info(f"Created database engine: {engine_type}")
    
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the session factory.
    
    Returns:
        SQLAlchemy session factory
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)
        logger.debug("Created session factory")
    
    return _session_factory


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        SQLAlchemy session
    """
    session_factory = get_session_factory()
    return session_factory()


@contextmanager
def session_scope():
    """
    Context manager for database sessions.
    
    Yields:
        SQLAlchemy session
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_connections():
    """
    Close all database connections.
    """
    global _engine, _session_factory, _session
    
    if _session:
        _session.close()
        _session = None
    
    if _engine:
        _engine.dispose()
        _engine = None
    
    _session_factory = None
    
    logger.info("Closed all database connections")


def create_tables():
    """
    Create all database tables.
    """
    from .models import Model
    
    engine = get_engine()
    Model.metadata.create_all(engine)
    logger.info("Created all database tables")


def drop_tables():
    """
    Drop all database tables.
    """
    from .models import Model
    
    engine = get_engine()
    Model.metadata.drop_all(engine)
    logger.info("Dropped all database tables")
