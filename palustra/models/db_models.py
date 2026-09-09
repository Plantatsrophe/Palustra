"""SQLAlchemy 2.0 database models for botanical taxonomy and USACE ratings."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy 2.0 models."""
    pass

class Taxon(Base):
    """Botanical taxon representing accepted USDA PLANTS entities harmonized with USACE ratings."""

    __tablename__ = "taxa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    raw_scientific_name: Mapped[str] = mapped_column(Text, nullable=False)
    clean_scientific_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    species_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    genus: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    species_epithet: Mapped[str] = mapped_column(String(100), nullable=False)
    infraspecific_rank: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    infraspecific_epithet: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    authority: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    common_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    taxonomic_status: Mapped[str] = mapped_column(String(50), default="Accepted", nullable=False)
    nativity: Mapped[str] = mapped_column(String(50), default="Native", nullable=False)
    c_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hybrid_parentage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Denormalized quick-access regional ratings
    nwpl_indicator_emp: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    nwpl_indicator_agcp: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship to detailed regional indicators
    regional_indicators: Mapped[List["RegionalIndicator"]] = relationship(
        "RegionalIndicator", back_populates="taxon", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_taxa_clean_genus", "genus", "species_epithet"),
    )

    def __repr__(self) -> str:
        return f"<Taxon(symbol='{self.symbol}', scientific_name='{self.clean_scientific_name}')>"

class RegionalIndicator(Base):
    """Detailed USACE NWPL regional indicator ratings per taxon."""

    __tablename__ = "regional_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taxon_id: Mapped[int] = mapped_column(Integer, ForeignKey("taxa.id", ondelete="CASCADE"), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(20), nullable=False)  # 'EMP' or 'AGCP'
    indicator_status: Mapped[str] = mapped_column(String(10), nullable=False)  # 'OBL', 'FACW', 'FAC', 'FACU', 'UPL', 'NL'
    source_scientific_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    matched_level: Mapped[str] = mapped_column(String(50), default="direct", nullable=False)  # 'direct', 'species_fallback', 'genus_uniform'

    taxon: Mapped["Taxon"] = relationship("Taxon", back_populates="regional_indicators")

    __table_args__ = (
        Index("ix_regional_taxon_region", "taxon_id", "region", unique=True),
        Index("ix_regional_region_status", "region", "indicator_status"),
    )

    def __repr__(self) -> str:
        return f"<RegionalIndicator(region='{self.region}', status='{self.indicator_status}')>"

class IngestionLog(Base):
    """Audit trail for ETL ingestion runs."""

    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    records_read: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
