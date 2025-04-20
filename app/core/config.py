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
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/login/google/callback"
    
    # Storage
    STORAGE_TYPE: str = "supabase"
    UPLOAD_FOLDER: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
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
    
    @validator("MAX_UPLOAD_SIZE", pre=True)
    def parse_max_upload_size(cls, v):
        if isinstance(v, str):
            try:
                return int(v.split("#")[0].strip())
            except (ValueError, IndexError):
                return 10485760  # 10MB
        return v
    
    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if not self.SQLALCHEMY_DATABASE_URI and self.POSTGRES_DB:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )

settings = Settings() 