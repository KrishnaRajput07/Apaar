from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg://apaar:apaar_secret@localhost:5432/apaar"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "apaar-pramaan-dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480   # 8 hours

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173"

    # Adapters
    APAAR_MOCK_URL: str = "http://localhost:8001"

    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "APAAR Pramaan"
    APP_VERSION: str = "1.0.0"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
