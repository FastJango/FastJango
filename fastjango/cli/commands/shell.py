"""
Shell command for FastJango - provides an interactive Python shell.
"""

import os
import sys
import code
import readline
import rlcompleter
from pathlib import Path
from typing import Optional, Dict, Any

from fastjango.core.logging import get_logger

logger = get_logger(__name__)


def get_shell_environment() -> Dict[str, Any]:
    """
    Get the environment variables and objects to make available in the shell.
    
    Returns:
        Dictionary of objects to make available in the shell
    """
    env = {}
    
    try:
        # Import FastJango core modules
        from fastjango.db import (
            Model, Manager, QuerySet,
            CharField, TextField, IntegerField, BigIntegerField,
            SmallIntegerField, PositiveIntegerField, PositiveSmallIntegerField,
            FloatField, DecimalField, BooleanField, NullBooleanField,
            DateField, DateTimeField, TimeField, DurationField,
            BinaryField, FileField, ImageField, FilePathField,
            EmailField, URLField, SlugField, UUIDField, IPAddressField,
            GenericIPAddressField, CommaSeparatedIntegerField,
            ForeignKey, OneToOneField, ManyToManyField,
            Migration, MigrationOperation,
            get_engine, get_session, close_connections,
            DatabaseError, IntegrityError, OperationalError,
            ProgrammingError, DataError, NotSupportedError,
            # SQLAlchemy compatibility
            SQLAlchemyModel, SQLAlchemyField, SQLAlchemyCharField, SQLAlchemyTextField,
            SQLAlchemyIntegerField, SQLAlchemyBigIntegerField, SQLAlchemyFloatField,
            SQLAlchemyBooleanField, SQLAlchemyDateField, SQLAlchemyDateTimeField,
            SQLAlchemyTimeField, SQLAlchemyBinaryField, SQLAlchemyDecimalField,
            SQLAlchemyUUIDField, SQLAlchemyForeignKey,
            create_sqlalchemy_model, register_sqlalchemy_model,
            SACharField, SATextField, SAIntegerField, SABigIntegerField,
            SASmallIntegerField, SAFloatField, SABooleanField, SADateField,
            SADateTimeField, SATimeField, SABinaryField, SADecimalField,
            SAUUIDField, SAForeignKey, relationship
        )
        
        env.update({
            # Database models and fields
            'Model': Model,
            'Manager': Manager,
            'QuerySet': QuerySet,
            'CharField': CharField,
            'TextField': TextField,
            'IntegerField': IntegerField,
            'BigIntegerField': BigIntegerField,
            'SmallIntegerField': SmallIntegerField,
            'PositiveIntegerField': PositiveIntegerField,
            'PositiveSmallIntegerField': PositiveSmallIntegerField,
            'FloatField': FloatField,
            'DecimalField': DecimalField,
            'BooleanField': BooleanField,
            'NullBooleanField': NullBooleanField,
            'DateField': DateField,
            'DateTimeField': DateTimeField,
            'TimeField': TimeField,
            'DurationField': DurationField,
            'BinaryField': BinaryField,
            'FileField': FileField,
            'ImageField': ImageField,
            'FilePathField': FilePathField,
            'EmailField': EmailField,
            'URLField': URLField,
            'SlugField': SlugField,
            'UUIDField': UUIDField,
            'IPAddressField': IPAddressField,
            'GenericIPAddressField': GenericIPAddressField,
            'CommaSeparatedIntegerField': CommaSeparatedIntegerField,
            'ForeignKey': ForeignKey,
            'OneToOneField': OneToOneField,
            'ManyToManyField': ManyToManyField,
            'Migration': Migration,
            'MigrationOperation': MigrationOperation,
            'get_engine': get_engine,
            'get_session': get_session,
            'close_connections': close_connections,
            'DatabaseError': DatabaseError,
            'IntegrityError': IntegrityError,
            'OperationalError': OperationalError,
            'ProgrammingError': ProgrammingError,
            'DataError': DataError,
            'NotSupportedError': NotSupportedError,
            # SQLAlchemy compatibility
            'SQLAlchemyModel': SQLAlchemyModel,
            'SQLAlchemyField': SQLAlchemyField,
            'SQLAlchemyCharField': SQLAlchemyCharField,
            'SQLAlchemyTextField': SQLAlchemyTextField,
            'SQLAlchemyIntegerField': SQLAlchemyIntegerField,
            'SQLAlchemyBigIntegerField': SQLAlchemyBigIntegerField,
            'SQLAlchemyFloatField': SQLAlchemyFloatField,
            'SQLAlchemyBooleanField': SQLAlchemyBooleanField,
            'SQLAlchemyDateField': SQLAlchemyDateField,
            'SQLAlchemyDateTimeField': SQLAlchemyDateTimeField,
            'SQLAlchemyTimeField': SQLAlchemyTimeField,
            'SQLAlchemyBinaryField': SQLAlchemyBinaryField,
            'SQLAlchemyDecimalField': SQLAlchemyDecimalField,
            'SQLAlchemyUUIDField': SQLAlchemyUUIDField,
            'SQLAlchemyForeignKey': SQLAlchemyForeignKey,
            'create_sqlalchemy_model': create_sqlalchemy_model,
            'register_sqlalchemy_model': register_sqlalchemy_model,
            'SACharField': SACharField,
            'SATextField': SATextField,
            'SAIntegerField': SAIntegerField,
            'SABigIntegerField': SABigIntegerField,
            'SASmallIntegerField': SASmallIntegerField,
            'SAFloatField': SAFloatField,
            'SABooleanField': SABooleanField,
            'SADateField': SADateField,
            'SADateTimeField': SADateTimeField,
            'SATimeField': SATimeField,
            'SABinaryField': SABinaryField,
            'SADecimalField': SADecimalField,
            'SAUUIDField': SAUUIDField,
            'SAForeignKey': SAForeignKey,
            'relationship': relationship,
        })
        
    except ImportError as e:
        logger.warning(f"Could not import database modules: {e}")
    
    try:
        # Import HTTP utilities
        from fastjango.http import JsonResponse, HttpResponse, TemplateResponse, redirect
        
        env.update({
            'JsonResponse': JsonResponse,
            'HttpResponse': HttpResponse,
            'TemplateResponse': TemplateResponse,
            'redirect': redirect,
        })
        
    except ImportError as e:
        logger.warning(f"Could not import HTTP modules: {e}")
    
    try:
        # Import URL utilities
        from fastjango.urls import path, include, Path, Include
        
        env.update({
            'path': path,
            'include': include,
            'Path': Path,
            'Include': Include,
        })
        
    except ImportError as e:
        logger.warning(f"Could not import URL modules: {e}")
    
    try:
        # Import core exceptions
        from fastjango.core.exceptions import (
            FastJangoError, ValidationError, DatabaseError,
            ObjectDoesNotExist, MultipleObjectsReturned
        )
        
        env.update({
            'FastJangoError': FastJangoError,
            'ValidationError': ValidationError,
            'DatabaseError': DatabaseError,
            'ObjectDoesNotExist': ObjectDoesNotExist,
            'MultipleObjectsReturned': MultipleObjectsReturned,
        })
        
    except ImportError as e:
        logger.warning(f"Could not import exception modules: {e}")
    
    try:
        # Import authentication utilities
        from fastjango.core.dependencies import get_current_user, get_required_user
        
        env.update({
            'get_current_user': get_current_user,
            'get_required_user': get_required_user,
        })
        
    except ImportError as e:
        logger.warning(f"Could not import authentication modules: {e}")
    
    # Add standard library imports
    env.update({
        'os': os,
        'sys': sys,
        'Path': Path,
        'datetime': __import__('datetime'),
        'time': __import__('time'),
        'json': __import__('json'),
        'pprint': __import__('pprint'),
    })
    
    # Try to import settings if available
    try:
        settings_module = os.environ.get('FASTJANGO_SETTINGS_MODULE')
        if settings_module:
            settings = __import__(settings_module)
            env['settings'] = settings
            
            # Add installed apps models if available
            if hasattr(settings, 'INSTALLED_APPS'):
                for app in settings.INSTALLED_APPS:
                    try:
                        # Try to import models from the app
                        models_module = __import__(f"{app}.models", fromlist=['*'])
                        env[app] = models_module
                        logger.info(f"Loaded models from {app}")
                    except ImportError:
                        logger.debug(f"Could not import models from {app}")
                        
    except ImportError as e:
        logger.warning(f"Could not import settings: {e}")
    
    return env


def run_shell(plain: bool = False, command: Optional[str] = None) -> None:
    """
    Run the FastJango shell.
    
    Args:
        plain: If True, run a plain Python shell without readline
        command: If provided, execute this command and exit
    """
    # Set up readline for better shell experience
    if not plain:
        try:
            readline.parse_and_bind("tab: complete")
            readline.set_completer(rlcompleter.Completer(get_shell_environment()).complete)
        except ImportError:
            logger.warning("readline not available, using basic shell")
            plain = True
    
    # Get the shell environment
    env = get_shell_environment()
    
    # Add some helpful variables
    env.update({
        '__name__': '__main__',
        '__doc__': 'FastJango Interactive Shell',
    })
    
    # Print welcome message
    print("FastJango Interactive Shell")
    print("=" * 40)
    print("Available objects:")
    print("- Database: Model, QuerySet, CharField, ForeignKey, etc.")
    print("- HTTP: JsonResponse, HttpResponse, TemplateResponse, redirect")
    print("- URLs: path, include, Path, Include")
    print("- Core: settings, ValidationError, DatabaseError, etc.")
    print("- SQLAlchemy: SQLAlchemyModel, relationship, etc.")
    print("=" * 40)
    
    if command:
        # Execute the provided command
        try:
            exec(command, env)
        except Exception as e:
            print(f"Error executing command: {e}")
            sys.exit(1)
    else:
        # Start interactive shell
        try:
            # Use code.interact for a better interactive experience
            code.interact(
                banner="FastJango Interactive Shell (Python {})".format(sys.version.split()[0]),
                local=env,
                exitmsg="Goodbye!"
            )
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except EOFError:
            print("\nGoodbye!")


def shell_command(plain: bool = False, command: Optional[str] = None) -> None:
    """
    Command-line interface for the shell command.
    
    Args:
        plain: If True, run a plain Python shell
        command: If provided, execute this command and exit
    """
    try:
        run_shell(plain=plain, command=command)
    except Exception as e:
        logger.error(f"Error running shell: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FastJango Interactive Shell")
    parser.add_argument("--plain", action="store_true", help="Run a plain Python shell")
    parser.add_argument("--command", "-c", help="Execute a command and exit")
    
    args = parser.parse_args()
    shell_command(plain=args.plain, command=args.command)
