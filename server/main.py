import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.database import Base, engine
from server.routers import auth_router, message_router, stream_router
from server.routers.group_router import router as group_router
from server.logging_config import configure_logging
from server import exceptions as app_exceptions

logger = configure_logging()

from typing import Optional, AsyncGenerator

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifetime context for the FastAPI app.

    Creates DB tables on startup if they are missing.
    """
    logger.info("Initializing database schema (if needed)")
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Secure Messenger \u2014 Stage 2",
    description="Authenticated, encrypted REST API with real-time SSE messaging",
    version="2.0.0",
    lifespan=lifespan,
)

import os

# Configure CORS origins via ALLOWED_ORIGINS env var (comma-separated).
# Defaults to the local dev origin used by the React app.
allowed = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5173')
raw_origins = [o.strip() for o in allowed.split(',') if o.strip()]

# Support a wildcard '*' to allow any origin. If wildcard is used, disallow
# credentialed requests (browsers reject Access-Control-Allow-Credentials: true
# with a wildcard origin). Prefer listing explicit origins in production.
if len(raw_origins) == 1 and raw_origins[0] == '*':
    allow_origins = ['*']
    allow_credentials = False
    logger.warning("CORS configured with wildcard '*' origin. Credentials are disabled.")
else:
    allow_origins = raw_origins
    allow_credentials = True

logger.info("CORS allowed origins=%s allow_credentials=%s", allow_origins, allow_credentials)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(app_exceptions.AppError)
async def app_error_handler(request: Request, exc: app_exceptions.AppError) -> JSONResponse:
    """Handle AppError exceptions and return JSON response with mapped status."""
    status, detail = app_exceptions.map_app_error_to_http(exc)
    logger.warning("Handled AppError: %s %s", status, detail)
    return JSONResponse(status_code=status, content={"detail": detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler: log and return HTTP 500 to the client."""
    # Log unexpected exceptions
    logger.exception("Unhandled exception in request %s %s", request.method, request.url)
    # Convert to generic 500 for clients
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


app.include_router(auth_router)
app.include_router(message_router)
app.include_router(stream_router)
app.include_router(group_router)

