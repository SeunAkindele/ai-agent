# config.py

from pydantic import BaseSettings, field_validator
from pydantic_settings import SettingsConfigDict
import os

class Settings(BaseSettings):
    app_name: str = "ingest-service"
    environment: str = "dev"
    log_level: str = "INFO"
    http_port: int = 8001
    
    # Security
    internal_mcp_token: str
    allowed_mcp_origins_raw: str = "http://gateway-api.internal"

    # Database
    postgres_dsn: str
    pgvector_dimension: int = 128  # Ensure vector dimension for embeddings is correctly defined

    # Ingestion settings
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.0
    max_context_chars: int = 6000

    # Providers
    embedding_provider: str = "hash"
    generator_provider: str = "stub"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_mcp_origins(self) -> set[str]:
        return {x.strip() for x in self.allowed_mcp_origins_raw.split(",") if x.strip()}

    @field_validator("pgvector_dimension")
    @classmethod
    def validate_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("pgvector_dimension must be > 0")
        return value


settings = Settings()