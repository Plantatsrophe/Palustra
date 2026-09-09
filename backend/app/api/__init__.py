"""API package exporting FastAPI application instance and router."""

from palustra.api.app import app, create_app
from palustra.api.routes import router

__all__ = ["app", "create_app", "router"]
