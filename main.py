import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from config import settings
from database import init_db, get_db
from auth import create_admin_user

# Import routers
from routers import auth_router, admin_router, qm_router, team_router, display_router
from routers import ws_router, media_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Quiz System...")

    # Create media directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.slides_dir, exist_ok=True)
    os.makedirs(settings.thumbs_dir, exist_ok=True)

    # Initialize database
    await init_db()
    print("Database initialized")

    # Create default admin user
    async for db in get_db():
        await create_admin_user(db)
        break

    print(f"Server starting on {settings.host}:{settings.port}")

    yield

    # Shutdown
    print("Shutting down Quiz System...")


# Create FastAPI app
app = FastAPI(
    title="Quiz System API",
    description="Real-time quiz system with buzzer and scoring",
    version="1.0.0",
    lifespan=lifespan
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path == "/api/admin/users/quiz-master":
        body = await request.body()
        print(f"[DEBUG] Quiz Master Creation Request:")
        print(f"  Method: {request.method}")
        print(f"  Path: {request.url.path}")
        print(f"  Headers: {dict(request.headers)}")
        print(f"  Body: {body.decode('utf-8') if body else 'empty'}")

        # Important: Create new request with the same body
        from fastapi import Request as FastAPIRequest
        async def receive():
            return {"type": "http.request", "body": body}

        request = FastAPIRequest(request.scope, receive)

    response = await call_next(request)
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[DEBUG] Validation Error on {request.url.path}:")
    print(f"  Errors: {exc.errors()}")
    print(f"  Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)}
    )

# Mount static files
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
app.include_router(media_router.router, prefix="/api/admin", tags=["Media"])
app.include_router(qm_router.router, prefix="/api/qm", tags=["Quiz Master"])
app.include_router(team_router.router, prefix="/api/team", tags=["Team"])
app.include_router(display_router.router, prefix="/api/display", tags=["Display"])
app.include_router(ws_router.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings
    })


@app.get("/admin/login")
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "settings": settings
    })


@app.get("/qm/login")
async def qm_login_page(request: Request):
    """Quiz Master login page"""
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "settings": settings
    })


@app.get("/team/login")
async def team_login_page(request: Request):
    """Team login page"""
    return templates.TemplateResponse("team_login.html", {
        "request": request,
        "settings": settings
    })


@app.get("/presenter/login")
async def presenter_login_page(request: Request):
    """Presenter login page"""
    return templates.TemplateResponse("presenter_login.html", {
        "request": request,
        "settings": settings
    })


@app.get("/admin/dashboard")
async def admin_dashboard_page(request: Request):
    """Admin dashboard page"""
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "settings": settings
    })


@app.get("/qm/dashboard")
async def qm_dashboard_page(request: Request):
    """Quiz Master dashboard page"""
    return templates.TemplateResponse("qm_dashboard.html", {
        "request": request,
        "settings": settings
    })


@app.get("/presenter/dashboard")
async def presenter_dashboard_page(request: Request):
    """Presenter dashboard page"""
    return templates.TemplateResponse("presenter_dashboard.html", {
        "request": request,
        "settings": settings
    })


@app.get("/team/interface")
async def team_interface_page(request: Request):
    """Team interface page"""
    return templates.TemplateResponse("team_interface.html", {
        "request": request,
        "settings": settings
    })


@app.get("/display")
async def display_page(request: Request):
    """Main display screen page"""
    return templates.TemplateResponse("display.html", {
        "request": request,
        "settings": settings
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}
