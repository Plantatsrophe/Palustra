"""Pytest fixtures and configuration for Palustra test suite."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.db_models import Base, Taxon, RegionalIndicator
from app.db.fts import init_fts5, rebuild_fts5
from app.db.session import get_db
from app.api.app import app
from app.etl.cache import LocalFieldCache

@pytest.fixture
def in_memory_engine():
    """Create an isolated in-memory SQLite engine with FTS5 enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        init_fts5(conn)
        conn.commit()
    return engine

@pytest.fixture
def db_session(in_memory_engine):
    """Provide a transactional session over the in-memory engine."""
    SessionFactory = sessionmaker(
        autocommit=False, autoflush=False, bind=in_memory_engine, expire_on_commit=False
    )
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def seeded_db_session(db_session, in_memory_engine):
    """Provide a session pre-seeded with representative botanical taxa."""
    sample_taxa = [
        Taxon(
            symbol="ACRU",
            raw_scientific_name="Acer rubrum L.",
            clean_scientific_name="Acer rubrum",
            species_name="Acer rubrum",
            genus="Acer",
            species_epithet="rubrum",
            infraspecific_rank=None,
            infraspecific_epithet=None,
            authority="L.",
            common_name="red maple",
            family="Sapindaceae",
            taxonomic_status="Accepted",
            nativity="Native",
            c_value=3,
            nwpl_indicator_emp="FAC",
            nwpl_indicator_agcp="FAC",
        ),
        Taxon(
            symbol="ACNE2",
            raw_scientific_name="Acer negundo L.",
            clean_scientific_name="Acer negundo",
            species_name="Acer negundo",
            genus="Acer",
            species_epithet="negundo",
            infraspecific_rank=None,
            infraspecific_epithet=None,
            authority="L.",
            common_name="boxelder",
            family="Sapindaceae",
            taxonomic_status="Accepted",
            nativity="Native",
            c_value=3,
            nwpl_indicator_emp="FAC",
            nwpl_indicator_agcp="FAC",
        ),
        Taxon(
            symbol="ACNET",
            raw_scientific_name="Acer negundo L. var. texanum Pax",
            clean_scientific_name="Acer negundo var. texanum",
            species_name="Acer negundo",
            genus="Acer",
            species_epithet="negundo",
            infraspecific_rank="var.",
            infraspecific_epithet="texanum",
            authority="Pax",
            common_name="boxelder",
            family="Sapindaceae",
            taxonomic_status="Accepted",
            nativity="Native",
            c_value=3,
            nwpl_indicator_emp="FAC",
            nwpl_indicator_agcp="FAC",
        ),
        Taxon(
            symbol="CALU",
            raw_scientific_name="Carex lurida Wahlenb.",
            clean_scientific_name="Carex lurida",
            species_name="Carex lurida",
            genus="Carex",
            species_epithet="lurida",
            infraspecific_rank=None,
            infraspecific_epithet=None,
            authority="Wahlenb.",
            common_name="shallow sedge",
            family="Cyperaceae",
            taxonomic_status="Accepted",
            nativity="Native",
            c_value=5,
            nwpl_indicator_emp="OBL",
            nwpl_indicator_agcp="OBL",
        ),
        Taxon(
            symbol="QUNI",
            raw_scientific_name="Quercus nigra L.",
            clean_scientific_name="Quercus nigra",
            species_name="Quercus nigra",
            genus="Quercus",
            species_epithet="nigra",
            infraspecific_rank=None,
            infraspecific_epithet=None,
            authority="L.",
            common_name="water oak",
            family="Fagaceae",
            taxonomic_status="Accepted",
            nativity="Native",
            c_value=5,
            nwpl_indicator_emp="FAC",
            nwpl_indicator_agcp="FACW",
        ),
        Taxon(
            symbol="TYLA",
            raw_scientific_name="Typha latifolia L.",
            clean_scientific_name="Typha latifolia",
            species_name="Typha latifolia",
            genus="Typha",
            species_epithet="latifolia",
            infraspecific_rank=None,
            infraspecific_epithet=None,
            authority="L.",
            common_name="broadleaf cattail",
            family="Typhaceae",
            taxonomic_status="Accepted",
            nativity="Native",
            c_value=1,
            nwpl_indicator_emp="OBL",
            nwpl_indicator_agcp="OBL",
        ),
        Taxon(
            symbol="ROPS",
            raw_scientific_name="Robinia pseudoacacia L.",
            clean_scientific_name="Robinia pseudoacacia",
            species_name="Robinia pseudoacacia",
            genus="Robinia",
            species_epithet="pseudoacacia",
            infraspecific_rank=None,
            infraspecific_epithet=None,
            authority="L.",
            common_name="black locust",
            family="Fabaceae",
            taxonomic_status="Accepted",
            nativity="Introduced",
            c_value=0,
            nwpl_indicator_emp="FACU",
            nwpl_indicator_agcp="UPL",
        ),
    ]

    db_session.add_all(sample_taxa)
    db_session.commit()

    # Rebuild FTS index for seeded records
    with in_memory_engine.connect() as conn:
        rebuild_fts5(conn)
        conn.commit()

    return db_session

@pytest.fixture
def client(seeded_db_session):
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        try:
            yield seeded_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_cache(tmp_path):
    """Isolated local field cache instance using temporary directory."""
    return LocalFieldCache(max_size=10, ttl_seconds=2, cache_dir=tmp_path)
