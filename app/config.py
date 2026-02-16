"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import List
import json
import tempfile


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://prismid:prismid_secret@localhost:5432/prismid_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-string"
    JWT_REFRESH_SECRET_KEY: str = "change-this-refresh-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_EXPIRY_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REFRESH_EXPIRY_DAYS: int = 7

    # ID Generation
    ID_SALT: str = "change-this-to-a-unique-secret-salt"

    # Google Sheets
    GOOGLE_SHEETS_ENABLED: bool = False
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "credentials/service_account.json"
    GOOGLE_CREDENTIALS_PATH: str = "credentials/service_account.json"
    GOOGLE_SHEET_ID: str = ""

    # Excel
    EXCEL_EXPORT_DIR: str = tempfile.gettempdir()

    # App
    APP_NAME: str = "PRISMID"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    ALLOWED_HOSTS: str = ""  # Comma-separated; empty = disabled (allow all)

    # Superadmin Seed
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_PASSWORD: str = "Prismid@2026"

    @property
    def cors_origins_list(self) -> List[str]:
        # Support both JSON array and comma-separated formats
        origins = self.CORS_ORIGINS.strip()
        if origins.startswith("["):
            return json.loads(origins)
        return [o.strip() for o in origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        if not self.ALLOWED_HOSTS.strip():
            return []
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
