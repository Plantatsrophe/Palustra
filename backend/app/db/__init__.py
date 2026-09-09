"""Database package exporting session, engine, and FTS5 search."""

from app.db.session import (
    engine,
    SessionFactory,
    init_db,
    get_db,
    get_db_context,
    create_db_engine,
)
from app.db.fts import (
    init_fts5,
    rebuild_fts5,
    search_taxa,
)

__all__ = [
    "engine",
    "SessionFactory",
    "init_db",
    "get_db",
    "get_db_context",
    "create_db_engine",
    "init_fts5",
    "rebuild_fts5",
    "search_taxa",
]
