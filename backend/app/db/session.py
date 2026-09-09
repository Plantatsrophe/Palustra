"""Database engine, session management, and SQLite connection initialization."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from palustra.config import settings
from palustra.models.db_models import Base
from palustra.db.fts import init_fts5

def create_db_engine(db_url: str = settings.database_url, is_memory: bool = False):
    """Create a configured SQLAlchemy 2.0 engine for SQLite."""
    connect_args = {"check_same_thread": False}
    
    if is_memory or ":memory:" in db_url:
        engine = create_engine(
            db_url,
            connect_args=connect_args,
            poolclass=StaticPool,
            future=True,
        )
    else:
        # Ensure parent directory exists
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            db_url,
            connect_args=connect_args,
            future=True,
        )

    # Configure SQLite PRAGMAs on connect
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            if not is_memory and ":memory:" not in db_url:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
        finally:
            cursor.close()

    return engine

engine = create_db_engine()
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def init_db(target_engine=None):
    """Create all relational tables and initialize FTS5 trigram virtual tables."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    with eng.connect() as conn:
        init_fts5(conn)
        conn.commit()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional session."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def get_db_context(target_engine=None) -> Generator[Session, None, None]:
    """Context manager for standalone scripts, testing, and ETL."""
    factory = sessionmaker(
        autocommit=False, autoflush=False, bind=target_engine or engine, expire_on_commit=False
    )
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
