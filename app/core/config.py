from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr, validator
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "GuardaDocs"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./guarda_docs.db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "uploads"
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    EMAILS_FROM_NAME: str = ""
    
    @validator("UPLOAD_FOLDER")
    def create_upload_folder(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL

settings = Settings() 