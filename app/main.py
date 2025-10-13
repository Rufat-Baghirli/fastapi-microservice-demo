# app/main.py
from contextlib import asynccontextmanager
import asyncio
import time
import socket

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from sqlalchemy import text

from app.core.config import settings
from app.core.logger import logger
from app.api.v1.api_router import api_router
from app.db.session import engine

# Lifespan — migrations on startup + engine disposal on shutdown
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

    # Dispose DB engine on shutdown
    await engine.dispose()
    print("Database engine disposed")

# App instance
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
    ],
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# Include routers
app.include_router(api_router)

# Utility endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring: DB and Redis/Rabbit."""
    info = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "service": settings.APP_NAME,
        "checks": {}
    }

    # DB check (simple query)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        info["checks"]["database"] = "ok"
    except Exception as e:
        info["checks"]["database"] = f"error: {str(e)}"
        info["status"] = "degraded"

    # Redis / TCP check (basic, non-blocking)
    try:
        # parse host:port from REDIS_URL like redis://host:port/0
        redis_host = settings.REDIS_URL.split("://")[-1].split(":")[0]
        redis_port = int(settings.REDIS_URL.split(":")[-1].split("/")[0])
        fut = asyncio.get_event_loop().run_in_executor(
            None,
            lambda: socket.create_connection((redis_host, redis_port), timeout=2)
        )
        fut.result(timeout=3)
        info["checks"]["redis"] = "ok"
    except Exception as e:
        info["checks"]["redis"] = f"error: {str(e)}"
        info["status"] = "degraded"

    return info

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

# Middlewares for headers and timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Return Pydantic validation errors in JSON
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Optional: run with 'python -m uvicorn app.main:app --reload' or add below block
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
