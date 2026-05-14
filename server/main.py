import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from server.database import Base, engine
from server.routers import auth_router, message_router, stream_router
from server.logging_config import configure_logging
from server import exceptions as app_exceptions

logger = configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema (if needed)")
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Secure Messenger \u2014 Stage 2",
    description="Authenticated, encrypted REST API with real-time SSE messaging",
    version="2.0.0",
    lifespan=lifespan,
)

@app.exception_handler(app_exceptions.AppError)
async def app_error_handler(request: Request, exc: app_exceptions.AppError):
    status, detail = app_exceptions.map_app_error_to_http(exc)
    logger.warning("Handled AppError: %s %s", status, detail)
    return JSONResponse(status_code=status, content={"detail": detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log unexpected exceptions
    logger.exception("Unhandled exception in request %s %s", request.method, request.url)
    # Convert to generic 500 for clients
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


app.include_router(auth_router)
app.include_router(message_router)
app.include_router(stream_router)

