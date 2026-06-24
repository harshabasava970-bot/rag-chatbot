"""
FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Run via Docker:
    docker-compose up
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes import router
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    settings = get_settings()

    # Ensure the upload directory exists
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting RAG Document Search API  (env={settings.app_env})")
    logger.info(f"Vector store: FAISS (local, free)")
    logger.info(f"CORS origins: {settings.cors_origins}")

    yield  # application runs here

    logger.info("Shutting down RAG Document Search API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="RAG Document Search API",
        description=(
            "Production-ready Retrieval-Augmented Generation API. "
            "Upload PDFs and ask questions about their content."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------
    # Middleware
    # -----------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # -----------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------
    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
