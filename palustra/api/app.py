"""FastAPI application initialization with lifespan and middleware."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from palustra.api.routes import router
from palustra.config import settings
from palustra.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager ensuring tables and FTS5 triggers exist."""
    init_db()
    yield

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Production-grade botanical ETL, SQLite FTS5 trigram fuzzy search, "
            "and taxonomic validation service harmonizing USDA PLANTS with USACE NWPL."
        ),
        lifespan=lifespan,
    )

    # Enable CORS for frontend and offline PWA integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app

app = create_app()
