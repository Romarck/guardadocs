from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr, validator
import os
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Storage
    STORAGE_TYPE: str = "supabase"
    UPLOAD_FOLDER: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
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
        case_sensitive = True
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"

settings = Settings() 