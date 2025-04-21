from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
import os
from pathlib import Path
import shutil
import uuid

def ensure_upload_folder():
    """Garante que a pasta de uploads existe."""
    upload_path = Path(settings.UPLOAD_FOLDER)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path

def get_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_FOLDER)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

def save_upload_file(file: UploadFile) -> tuple[str, str]:
    """
    Salva o arquivo enviado e retorna uma tupla com (nome_original, nome_storage)
    """
    original_filename = file.filename
    # Gera um nome único para o arquivo
    file_extension = os.path.splitext(original_filename)[1]
    storage_filename = f"{os.urandom(16).hex()}{file_extension}"
    
    # Salva o arquivo
    upload_dir = get_upload_dir()
    file_path = upload_dir / storage_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return original_filename, storage_filename

async def get_file_path(storage_filename: str) -> str:
    """
    Retorna o caminho absoluto do arquivo no sistema de arquivos
    """
    upload_dir = get_upload_dir()
    file_path = upload_dir / storage_filename
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {storage_filename}")
    return str(file_path.absolute())

async def delete_file(storage_filename: str) -> None:
    """
    Remove um arquivo do sistema de arquivos
    """
    upload_dir = get_upload_dir()
    file_path = upload_dir / storage_filename
    if file_path.exists():
        file_path.unlink() 