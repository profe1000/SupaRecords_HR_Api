from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/videodownloader"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # JWT
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # Email / Resend
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()
