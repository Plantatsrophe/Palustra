"""Configuration management for Palustra ETL and API service."""

from pathlib import Path
import os
from typing import Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "Data"

class Settings(BaseModel):
    """Application settings with environment variable fallback."""

    app_name: str = "Palustra Botanical ETL & Taxon Service"
    app_version: str = "0.1.0"
    debug: bool = Field(default_factory=lambda: os.getenv("PALUSTRA_DEBUG", "false").lower() == "true")

    # Database settings
    db_path: Path = Field(default_factory=lambda: Path(os.getenv("PALUSTRA_DB_PATH", str(PROJECT_ROOT / "palustra.db"))))
    
    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    # Data files
    usda_plants_path: Path = Field(default_factory=lambda: Path(os.getenv("PALUSTRA_USDA_PATH", str(DATA_DIR / "NC_USDA_PlantList.csv"))))
    nwpl_agcp_path: Path = Field(default_factory=lambda: Path(os.getenv("PALUSTRA_NWPL_AGCP_PATH", str(DATA_DIR / "2022_NWPL_AGCP.xlsx"))))
    nwpl_emp_path: Path = Field(default_factory=lambda: Path(os.getenv("PALUSTRA_NWPL_EMP_PATH", str(DATA_DIR / "2022_NWPL_EMP.xlsx"))))

    # Field Cache settings
    cache_max_size: int = Field(default_factory=lambda: int(os.getenv("PALUSTRA_CACHE_SIZE", "5000")))
    cache_ttl_seconds: int = Field(default_factory=lambda: int(os.getenv("PALUSTRA_CACHE_TTL", "3600")))
    cache_dir: Path = Field(default_factory=lambda: Path(os.getenv("PALUSTRA_CACHE_DIR", str(PROJECT_ROOT / ".cache"))))

    # API Settings
    api_host: str = Field(default_factory=lambda: os.getenv("PALUSTRA_API_HOST", "0.0.0.0"))
    api_port: int = Field(default_factory=lambda: int(os.getenv("PALUSTRA_API_PORT", "8000")))

    # Gemini 1.5 Flash AI Settings
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    field_note_confidence_threshold: float = Field(default_factory=lambda: float(os.getenv("PALUSTRA_FIELD_NOTE_CONFIDENCE_THRESHOLD", "0.75")))
    field_note_temperature: float = Field(default_factory=lambda: float(os.getenv("PALUSTRA_FIELD_NOTE_TEMP", "0.1")))

settings = Settings()
