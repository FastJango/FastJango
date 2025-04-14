"""
RunServer command - Runs the FastJango development server
"""

import os
import sys
import importlib
import logging
from pathlib import Path
import subprocess

from fastjango.core.logging import Logger

# Get logger
logger = Logger("fastjango.cli.commands.runserver")


def get_settings_module():
    """
    Get the settings module from the environment.
    
    Returns:
        The settings module name or None if not found
    """
    settings_module = os.environ.get("FASTJANGO_SETTINGS_MODULE")
    if not settings_module:
        # Try to find manage.py and extract settings module
        current_dir = Path.cwd()
        manage_py = current_dir / "manage.py"
        
        if manage_py.exists():
            with open(manage_py, "r") as f:
                content = f.read()
                
            # Extract default settings module using a simple string search
            # This is a simplified approach, not a full Python parser
            settings_line = [line for line in content.split("\n") 
                            if "os.environ.setdefault" in line and "SETTINGS_MODULE" in line]
            
            if settings_line:
                # Extract the settings module name from the line
                try:
                    # Find the string between quotes
                    import re
                    match = re.search(r'setdefault\(["\'].*["\'], ["\'](.+)["\']\)', settings_line[0])
                    if match:
                        settings_module = match.group(1)
                except Exception as e:
                    logger.error(f"Failed to extract settings module from manage.py: {e}")
    
    return settings_module


def run_server(host: str, port: int, reload: bool = True) -> None:
    """
    Run the FastJango development server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to enable auto-reload
    
    Raises:
        RuntimeError: If the server fails to start
    """
    try:
        # Find and import settings module
        settings_module = get_settings_module()
        
        if not settings_module:
            raise RuntimeError(
                "No settings module found. Set the FASTJANGO_SETTINGS_MODULE "
                "environment variable or run from a project directory with manage.py"
            )
        
        # Set environment variable for other processes
        os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", settings_module)
        
        # Extract project name from settings module
        project_name = settings_module.split('.')[0]
        
        # Build the ASGI application path for uvicorn
        asgi_app = f"{project_name}.asgi:application"
        
        # Log startup message
        logger.info(f"Starting development server at http://{host}:{port}/")
        logger.info("Quit the server with CONTROL-C.")
        
        # Start uvicorn directly with reload
        import uvicorn
        
        # Set log level based on logger level
        log_level = "info"
        if logger.logger.level <= logging.DEBUG:
            log_level = "debug"
        
        # Start uvicorn programmatically
        uvicorn.run(
            asgi_app,
            host=host,
            port=port,
            log_level=log_level,
            reload=reload,
        )
        
    except Exception as e:
        logger.error(f"Error starting development server: {e}", exc_info=True)
        raise RuntimeError(f"Failed to start server: {e}") 