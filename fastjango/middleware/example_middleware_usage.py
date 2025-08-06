"""
FastJango Middleware, Authentication, Session, and Media Example

This example demonstrates how to use all the new middleware, authentication,
session management, and media file handling features in FastJango.
"""

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

# Import FastJango components
from fastjango.middleware import (
    SessionMiddleware, AuthenticationMiddleware, SecurityMiddleware,
    CORSMiddleware, CommonMiddleware, MessageMiddleware, GZipMiddleware
)
from fastjango.middleware.session import get_session_data, set_session_data, clear_session
from fastjango.middleware.authentication import (
    get_user, is_authenticated, login, logout, login_required, staff_member_required
)
from fastjango.middleware.messages import (
    add_message, get_messages, success, error, info, warning
)
from fastjango.media import (
    MediaFileHandler, FileUploadHandler, ImageUploadHandler,
    FileSystemStorage, get_media_url, get_media_path
)


def create_example_app():
    """Create example FastJango app with all middleware features."""
    
    # Create FastAPI app
    app = FastAPI(title="FastJango Middleware Example")
    
    # Settings dictionary (similar to Django settings.py)
    settings = {
        # Session settings
        'SESSION_COOKIE_NAME': 'sessionid',
        'SESSION_COOKIE_AGE': 1209600,  # 2 weeks
        'SESSION_COOKIE_SECURE': False,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_EXPIRE_AT_BROWSER_CLOSE': False,
        'SESSION_SAVE_EVERY_REQUEST': False,
        
        # Security settings
        'SECURITY_HEADERS': {
            'X-Custom-Header': 'FastJango'
        },
        'ALLOWED_HOSTS': ['*'],
        'SECURE_SSL_REDIRECT': False,
        'SECURE_CONTENT_TYPE_NOSNIFF': True,
        'SECURE_BROWSER_XSS_FILTER': True,
        'SECURE_FRAME_DENY': True,
        'SECURE_CONTENT_SECURITY_POLICY': "default-src 'self'",
        'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
        'SECURE_HSTS_SECONDS': 31536000,
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
        'SECURE_HSTS_PRELOAD': False,
        
        # CORS settings
        'CORS_ALLOWED_ORIGINS': ['http://localhost:3000'],
        'CORS_ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'CORS_ALLOWED_HEADERS': ['*'],
        'CORS_ALLOW_CREDENTIALS': True,
        'CORS_MAX_AGE': 86400,
        
        # Common middleware settings
        'APPEND_SLASH': True,
        'REMOVE_TRAILING_SLASH': False,
        'COMMON_IGNORE_PATHS': ['/api/'],
        'LOG_REQUESTS': True,
        'LOG_RESPONSES': True,
        'USE_REQUEST_ID': True,
        'REQUEST_ID_HEADER': 'X-Request-ID',
        
        # Compression settings
        'USE_GZIP': True,
        'GZIP_COMPRESS_LEVEL': 6,
        'GZIP_MIN_SIZE': 200,
        'GZIP_CONTENT_TYPES': [
            'text/html', 'text/css', 'text/javascript',
            'application/javascript', 'application/json'
        ],
        
        # Media settings
        'MEDIA_ROOT': 'media',
        'MEDIA_URL': '/media/',
        'MEDIA_STORAGE': 'filesystem',
        'MEDIA_MAX_SIZE': 10 * 1024 * 1024,  # 10MB
        'MEDIA_ALLOWED_TYPES': ['*/*'],
        'MEDIA_SUBDIRECTORIES': ['images', 'documents', 'videos'],
        
        # Messages settings
        'MESSAGE_STORAGE': 'session',
        'MESSAGE_LEVEL': 'INFO'
    }
    
    # Set up middleware
    setup_middleware(app, settings)
    
    # Set up media handling
    setup_media_handling(app, settings)
    
    # Add example routes
    add_example_routes(app)
    
    return app


def setup_middleware(app: FastAPI, settings: dict):
    """Set up all middleware components."""
    
    # Session middleware
    session_middleware = SessionMiddleware(
        app,
        session_cookie_name=settings['SESSION_COOKIE_NAME'],
        session_cookie_age=settings['SESSION_COOKIE_AGE'],
        session_cookie_secure=settings['SESSION_COOKIE_SECURE'],
        session_cookie_httponly=settings['SESSION_COOKIE_HTTPONLY'],
        session_cookie_samesite=settings['SESSION_COOKIE_SAMESITE'],
        session_expire_at_browser_close=settings['SESSION_EXPIRE_AT_BROWSER_CLOSE'],
        session_save_every_request=settings['SESSION_SAVE_EVERY_REQUEST']
    )
    app.add_middleware(SessionMiddleware, **session_middleware.__dict__)
    
    # Authentication middleware
    auth_middleware = AuthenticationMiddleware(app)
    app.add_middleware(AuthenticationMiddleware, **auth_middleware.__dict__)
    
    # Security middleware
    security_middleware = SecurityMiddleware(
        app,
        security_headers=settings['SECURITY_HEADERS'],
        allowed_hosts=settings['ALLOWED_HOSTS'],
        secure_ssl_redirect=settings['SECURE_SSL_REDIRECT'],
        secure_content_type_nosniff=settings['SECURE_CONTENT_TYPE_NOSNIFF'],
        secure_browser_xss_filter=settings['SECURE_BROWSER_XSS_FILTER'],
        secure_frame_deny=settings['SECURE_FRAME_DENY'],
        secure_content_security_policy=settings['SECURE_CONTENT_SECURITY_POLICY'],
        secure_referrer_policy=settings['SECURE_REFERRER_POLICY'],
        secure_hsts_seconds=settings['SECURE_HSTS_SECONDS'],
        secure_hsts_include_subdomains=settings['SECURE_HSTS_INCLUDE_SUBDOMAINS'],
        secure_hsts_preload=settings['SECURE_HSTS_PRELOAD']
    )
    app.add_middleware(SecurityMiddleware, **security_middleware.__dict__)
    
    # CORS middleware
    cors_middleware = CORSMiddleware(
        app,
        allowed_origins=settings['CORS_ALLOWED_ORIGINS'],
        allowed_methods=settings['CORS_ALLOWED_METHODS'],
        allowed_headers=settings['CORS_ALLOWED_HEADERS'],
        allow_credentials=settings['CORS_ALLOW_CREDENTIALS'],
        max_age=settings['CORS_MAX_AGE']
    )
    app.add_middleware(CORSMiddleware, **cors_middleware.__dict__)
    
    # Common middleware
    common_middleware = CommonMiddleware(
        app,
        append_slash=settings['APPEND_SLASH'],
        remove_trailing_slash=settings['REMOVE_TRAILING_SLASH'],
        ignore_paths=settings['COMMON_IGNORE_PATHS'],
        process_request=True,
        process_response=True,
        process_exception=True
    )
    app.add_middleware(CommonMiddleware, **common_middleware.__dict__)
    
    # Message middleware
    message_middleware = MessageMiddleware(app)
    app.add_middleware(MessageMiddleware, **message_middleware.__dict__)
    
    # GZip middleware
    if settings['USE_GZIP']:
        gzip_middleware = GZipMiddleware(
            app,
            compress_level=settings['GZIP_COMPRESS_LEVEL'],
            min_size=settings['GZIP_MIN_SIZE'],
            content_types=settings['GZIP_CONTENT_TYPES']
        )
        app.add_middleware(GZipMiddleware, **gzip_middleware.__dict__)


def setup_media_handling(app: FastAPI, settings: dict):
    """Set up media file handling."""
    
    # Create media storage
    storage = FileSystemStorage(
        media_root=settings['MEDIA_ROOT'],
        media_url=settings['MEDIA_URL']
    )
    
    # Create media handlers
    global file_handler, image_handler
    file_handler = FileUploadHandler(
        storage=storage,
        max_size=settings['MEDIA_MAX_SIZE'],
        allowed_types=settings['MEDIA_ALLOWED_TYPES']
    )
    
    image_handler = ImageUploadHandler(
        storage=storage,
        max_size=5 * 1024 * 1024,  # 5MB for images
        max_width=1920,
        max_height=1080,
        quality=85
    )


def add_example_routes(app: FastAPI):
    """Add example routes demonstrating all features."""
    
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Home page with session and authentication info."""
        user = get_user(request)
        session_data = get_session_data(request, 'visit_count', 0)
        
        # Increment visit count
        set_session_data(request, 'visit_count', session_data + 1)
        
        # Add welcome message
        if not is_authenticated(request):
            info(request, "Welcome! Please log in to access all features.")
        else:
            success(request, f"Welcome back, {user.username}!")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FastJango Middleware Example</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .message {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .success {{ background-color: #d4edda; color: #155724; }}
                .info {{ background-color: #d1ecf1; color: #0c5460; }}
                .warning {{ background-color: #fff3cd; color: #856404; }}
                .error {{ background-color: #f8d7da; color: #721c24; }}
                .form {{ margin: 20px 0; }}
                .form input, .form button {{ margin: 5px; padding: 5px; }}
            </style>
        </head>
        <body>
            <h1>FastJango Middleware Example</h1>
            
            <h2>Session Information</h2>
            <p>Visit count: {session_data}</p>
            <p>User: {user.username if user else 'Not authenticated'}</p>
            
            <h2>Messages</h2>
            {render_messages_html(request)}
            
            <h2>Authentication</h2>
            <div class="form">
                <form method="post" action="/login">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
                
                <form method="post" action="/logout" style="display: inline;">
                    <button type="submit">Logout</button>
                </form>
            </div>
            
            <h2>File Upload</h2>
            <div class="form">
                <form method="post" action="/upload" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button type="submit">Upload File</button>
                </form>
                
                <form method="post" action="/upload/image" enctype="multipart/form-data">
                    <input type="file" name="file" accept="image/*" required>
                    <button type="submit">Upload Image</button>
                </form>
            </div>
            
            <h2>Staff Only Area</h2>
            <p><a href="/staff">Staff Dashboard</a> (requires staff access)</p>
            
            <h2>API Endpoints</h2>
            <ul>
                <li><a href="/api/session">Session Info</a></li>
                <li><a href="/api/user">User Info</a></li>
                <li><a href="/api/messages">Messages</a></li>
                <li><a href="/api/files">File List</a></li>
            </ul>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    
    @app.post("/login")
    async def login_view(request: Request):
        """Login endpoint."""
        form_data = await request.form()
        username = form_data.get('username')
        password = form_data.get('password')
        
        # Simple authentication (in real app, check against database)
        if username == "admin" and password == "password":
            from fastjango.middleware.authentication import User
            user = User(
                id=1,
                username=username,
                email=f"{username}@example.com",
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            login(request, user)
            success(request, f"Welcome, {username}!")
        else:
            error(request, "Invalid credentials!")
        
        from fastjango.http import redirect
        return redirect("/")
    
    @app.post("/logout")
    async def logout_view(request: Request):
        """Logout endpoint."""
        logout(request)
        info(request, "You have been logged out.")
        
        from fastjango.http import redirect
        return redirect("/")
    
    @app.get("/staff")
    @staff_member_required
    async def staff_dashboard(request: Request):
        """Staff-only dashboard."""
        user = get_user(request)
        success(request, f"Welcome to the staff dashboard, {user.username}!")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Staff Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .message {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .success {{ background-color: #d4edda; color: #155724; }}
            </style>
        </head>
        <body>
            <h1>Staff Dashboard</h1>
            <p>Welcome, {user.username}!</p>
            <p>This is a staff-only area.</p>
            
            <h2>Messages</h2>
            {render_messages_html(request)}
            
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    
    @app.post("/upload")
    async def upload_file(request: Request, file: UploadFile = File(...)):
        """File upload endpoint."""
        try:
            media_file = await file_handler.handle_upload(file)
            success(request, f"File uploaded successfully: {media_file.name}")
        except Exception as e:
            error(request, f"Upload failed: {str(e)}")
        
        from fastjango.http import redirect
        return redirect("/")
    
    @app.post("/upload/image")
    async def upload_image(request: Request, file: UploadFile = File(...)):
        """Image upload endpoint."""
        try:
            media_file = await image_handler.handle_upload(file)
            success(request, f"Image uploaded and processed: {media_file.name}")
        except Exception as e:
            error(request, f"Image upload failed: {str(e)}")
        
        from fastjango.http import redirect
        return redirect("/")
    
    # API endpoints
    @app.get("/api/session")
    async def api_session(request: Request):
        """Get session information."""
        session_data = get_session_data(request, 'visit_count', 0)
        return {
            "visit_count": session_data,
            "session_id": getattr(request.state, 'session_key', None)
        }
    
    @app.get("/api/user")
    async def api_user(request: Request):
        """Get user information."""
        user = get_user(request)
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser
            }
        return {"authenticated": False}
    
    @app.get("/api/messages")
    async def api_messages(request: Request):
        """Get messages."""
        from fastjango.middleware.messages import get_messages_json
        import json
        return json.loads(get_messages_json(request))
    
    @app.get("/api/files")
    async def api_files(request: Request):
        """Get uploaded files."""
        files = file_handler.list_files()
        return {"files": files}


def render_messages_html(request: Request) -> str:
    """Render messages as HTML."""
    from fastjango.middleware.messages import render_messages_html as render_messages
    return render_messages(request)


# Create the app
app = create_example_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)