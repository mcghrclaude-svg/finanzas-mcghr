"""
Application configuration — reads from environment variables.
All settings come from .env file or environment. Nothing hardcoded.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    env: str = "dev"  # dev | test | staging | prod

    # Database
    db_path: str = "data/dev/finanzas_dev.db"

    # Paths
    onedrive_path: str = "data/dev/onedrive"
    backup_path: str = "data/dev/backups"
    config_path: str = "config_correos.json"

    # External APIs
    anthropic_api_key: str = ""
    claude_provider: str = "real"  # real | mock

    # Mail
    mail_provider: str = "mock"  # gmail | imap | mock
    outlook_app_password: str = ""

    # Server
    backend_port: int = 8000
    frontend_port: int = 3000

    # CORS — frontend origins allowed
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",
        "http://192.168.1.0/24",  # red local para iPhone
    ]

    # Backup retention
    backup_retention_days: int = 90

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = os.getenv("ENV_FILE", ".env.dev")
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def db_url(self) -> str:
        if self.db_path == ":memory:":
            return "sqlite+aiosqlite:///:memory:"
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{path}"

    @property
    def is_test(self) -> bool:
        return self.env == "test"

    @property
    def is_production(self) -> bool:
        return self.env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
