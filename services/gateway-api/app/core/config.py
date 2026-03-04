from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gateway-api"
    environment: str = "dev"
    log_level: str = "INFO"
    api_prefix: str = "/v1"

    rag_mcp_url: str
    internal_mcp_token: str
    internal_mcp_origin: str = "http://gateway-api.internal"
    mcp_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()