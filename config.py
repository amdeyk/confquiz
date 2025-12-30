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

    # Conference/Event Details (must be set in .env)
    conference_name: str = Field(alias="CONFERENCE_NAME")
    conference_full_name: str = Field(default="", alias="CONFERENCE_FULL_NAME")
    conference_dates: str = Field(default="", alias="CONFERENCE_DATES")
    conference_venue: str = Field(default="", alias="CONFERENCE_VENUE")
    conference_chairperson: str = Field(default="", alias="CONFERENCE_CHAIRPERSON")
    conference_organizer: str = Field(default="", alias="CONFERENCE_ORGANIZER")
    conference_scientific_chair: str = Field(default="", alias="CONFERENCE_SCIENTIFIC_CHAIR")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
