from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time

from app.core.config import settings
from app.api.v1.api_router import api_router


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if settings.RUN_MIGRATIONS_ON_STARTUP:
        print("Running database migrations...")
        try:
            from app.db.migrations import run_migrations
            await run_migrations()
            print("Database migrations completed successfully")
        except Exception as e:
            print(f"Error running migrations: {e}")
            if settings.ENVIRONMENT == "production":
                raise

    yield

    from app.db.session import engine
    await engine.dispose()
    print("Database engine disposed")


# FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "users", "description": "User management"},
        {"name": "authentication", "description": "Auth operations"},
        {"name": "tasks", "description": "Background tasks"},
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "service": settings.APP_NAME
    }


# Root endpoint
@app.get("/")
async def root():
    """Application root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}!",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": settings.API_V1_STR
        }
    }


# Process time middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Middleware to add response time header"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Trusted host middleware (production)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )
