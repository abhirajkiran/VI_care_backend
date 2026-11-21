import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.redis import close_redis_client

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & Shutdown lifecycle hook."""
    yield
    try:
        await close_redis_client()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Unified Global Exception Handlers for Backend, Web, and Mobile Clients
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Standardize all HTTP exceptions so both mobile (Dio) and web (fetch)
    reliably receive unified 'message' and 'detail' fields.
    """
    detail_content = exc.detail
    message = str(detail_content) if not isinstance(detail_content, (dict, list)) else str(detail_content)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": message,
            "detail": detail_content,
            "status_code": exc.status_code,
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Format Pydantic schema validation errors with human-readable summary
    in 'message' and full field details in 'detail'.
    """
    errors = exc.errors()
    error_messages = []
    for err in errors:
        loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{loc}: {msg}" if loc else msg)

    clean_message = "; ".join(error_messages) if error_messages else "Request validation failed"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "message": clean_message,
            "detail": errors,
            "error_code": "VALIDATION_ERROR",
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all 500 handler preventing raw trace exposure while returning structured JSON.
    """
    logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected internal server error occurred. Please contact hospital support.",
            "detail": str(exc) if settings.DEBUG else "Internal Server Error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


# CORS setup for mobile and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aggregated v1 endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker & load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }
