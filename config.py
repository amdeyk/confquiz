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
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
