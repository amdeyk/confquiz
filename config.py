import os

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./quiz.db", alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Security
    secret_key: str = Field(default="your-secret-key-change-this", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Media Storage
    upload_dir: str = Field(default="./media/uploads", alias="UPLOAD_DIR")
    slides_dir: str = Field(default="./media/slides", alias="SLIDES_DIR")
    thumbs_dir: str = Field(default="./media/thumbs", alias="THUMBS_DIR")

    # PPT Conversion
    libreoffice_path: Optional[str] = Field(default=None, alias="LIBREOFFICE_PATH")

    # Admin Default
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="changeme", alias="ADMIN_PASSWORD")

    # LiveKit (SFU)
    livekit_url: str = Field(default="wss://livekit.example.com", alias="LIVEKIT_URL")
    livekit_api_key: str = Field(default="", alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(default="", alias="LIVEKIT_API_SECRET")
    livekit_token_ttl_seconds: int = Field(default=3600, alias="LIVEKIT_TOKEN_TTL_SECONDS")
    livekit_room_prefix: str = Field(default="quiz", alias="LIVEKIT_ROOM_PREFIX")

    # Bandwidth monitoring (VPS)
    bandwidth_monitor_enabled: bool = Field(default=True, alias="BANDWIDTH_MONITOR_ENABLED")
    bandwidth_interface: str = Field(default="eth0", alias="BANDWIDTH_INTERFACE")
    bandwidth_sample_interval_seconds: int = Field(default=60, alias="BANDWIDTH_SAMPLE_INTERVAL_SECONDS")
    bandwidth_budget_gb: int = Field(default=200, alias="BANDWIDTH_BUDGET_GB")
    bandwidth_warn_gb: int = Field(default=160, alias="BANDWIDTH_WARN_GB")
    bandwidth_critical_gb: int = Field(default=180, alias="BANDWIDTH_CRITICAL_GB")

    # Conference/Event Details (must be set in .env)
    conference_name: str = Field(alias="CONFERENCE_NAME")
    conference_full_name: str = Field(default="", alias="CONFERENCE_FULL_NAME")
    conference_dates: str = Field(default="", alias="CONFERENCE_DATES")
    conference_venue: str = Field(default="", alias="CONFERENCE_VENUE")
    conference_chairperson: str = Field(default="", alias="CONFERENCE_CHAIRPERSON")
    conference_organizer: str = Field(default="", alias="CONFERENCE_ORGANIZER")
    conference_scientific_chair: str = Field(default="", alias="CONFERENCE_SCIENTIFIC_CHAIR")

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        case_sensitive = False


settings = Settings()
