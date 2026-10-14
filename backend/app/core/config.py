from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Marketing Performance Analyzer"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "default-secret-key-for-development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/marketing_analyzer"

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TIMEOUT: float = 15.0
    GROQ_MAX_RETRIES: int = 2

    model_config = SettingsConfigDict(
        env_file=[
            ".env",
            "backend/.env",
        ],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()