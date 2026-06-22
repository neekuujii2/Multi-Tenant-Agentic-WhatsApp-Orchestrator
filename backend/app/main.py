"""
Main FastAPI Application Entrypoint.
Configures lifespan events, CORS, request middleware, routers, and health checks.
"""
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.mongo import connect_db, disconnect_db
from app.db.redis_client import connect_redis, disconnect_redis
from app.routers import webhook, dashboard
from app.utils.logger import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown hook events."""
    log.info("app_starting", environment=settings.environment)
    # Connect MongoDB
    try:
        await connect_db()
    except Exception as e:
        log.critical("mongodb_connection_failed", error=str(e))
        raise e

    # Connect Redis
    try:
        await connect_redis()
    except Exception as e:
        log.critical("redis_connection_failed", error=str(e))
        # Don't crash app if Redis is down (graceful fallback in retriever)
        pass

    yield

    # Clean shutdown
    await disconnect_db()
    await disconnect_redis()
    log.info("app_stopped")


app = FastAPI(
    title="Multi-Tenant Agentic WhatsApp Orchestrator",
    description="Scalable, production-ready WhatsApp automated customer support orchestrator powered by LangGraph.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to inject correlation IDs and trace response times.
    Logs every request with request path and status codes.
    """
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    # Store request_id in request state for logs correlation
    request.state.request_id = request_id

    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["x-request-id"] = request_id
    response.headers["x-process-time"] = f"{process_time:.4f}s"

    log.info(
        "request_processed",
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=int(process_time * 1000),
        request_id=request_id,
    )
    return response


# Include Routers
app.include_router(webhook.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker, Railway, and Kubernetes probes."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.environment,
    }
