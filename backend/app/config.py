"""
Application configuration using Pydantic Settings.
Loads from .env file in development, environment variables in production.
"""
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # Meta WhatsApp
    meta_verify_token: str
    meta_app_secret: str

    # LLM
    anthropic_api_key: str

    # Database
    mongodb_uri: str
    redis_url: str

    # App
    log_level: str = "INFO"
    environment: str = "development"
    cors_origins: List[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
