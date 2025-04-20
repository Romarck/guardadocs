from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
import os
import httpx
from datetime import datetime
from supabase import create_client, Client

BUCKET_NAME = "documentos"

def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

async def create_bucket_if_not_exists():
    """Cria o bucket de documentos se não existir."""
    async with httpx.AsyncClient() as client:
        # Verifica se o bucket existe
        response = await client.get(
            f"{settings.SUPABASE_URL}/storage/v1/bucket/{BUCKET_NAME}",
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "apikey": settings.SUPABASE_SERVICE_KEY
            }
        )
        
        if response.status_code == 404:
            # Bucket não existe, vamos criar
            create_response = await client.post(
                f"{settings.SUPABASE_URL}/storage/v1/bucket",
                headers={
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "name": BUCKET_NAME,
                    "public": False,
                    "file_size_limit": settings.MAX_UPLOAD_SIZE
                }
            )
            
            if create_response.status_code != 201:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao criar bucket: {create_response.text}"
                )
            
            # Habilita RLS
            rls_response = await client.post(
                f"{settings.SUPABASE_URL}/storage/v1/bucket/{BUCKET_NAME}/policy",
                headers={
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "name": "Enable RLS",
                    "definition": "true",
                    "check": "true"
                }
            )
            
            if rls_response.status_code != 201:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao habilitar RLS: {rls_response.text}"
                )
            
            # Cria política de acesso
            policy_response = await client.post(
                f"{settings.SUPABASE_URL}/storage/v1/bucket/{BUCKET_NAME}/policy",
                headers={
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "name": "Allow authenticated access",
                    "definition": "(auth.role() = 'authenticated')",
                    "check": "true",
                    "operation": "SELECT"
                }
            )
            
            if policy_response.status_code != 201:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao criar política de acesso: {policy_response.text}"
                )

async def ensure_documents_bucket():
    """Garante que o bucket de documentos existe."""
    try:
        await create_bucket_if_not_exists()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao configurar bucket: {str(e)}"
        )

async def upload_file(file_content: bytes, filename: str) -> str:
    """Faz upload de um arquivo para o bucket."""
    await ensure_documents_bucket()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}",
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Content-Type": "application/octet-stream"
            },
            content=file_content
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao fazer upload: {response.text}"
            )
        
        return filename

async def delete_file(filename: str):
    """Deleta um arquivo do bucket."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}",
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "apikey": settings.SUPABASE_SERVICE_KEY
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao deletar arquivo: {response.text}"
            )

async def get_file_url(filename: str, expires_in: int = 3600) -> str:
    """Gera uma URL assinada para acessar o arquivo."""
    print(f"Gerando URL para o arquivo: {filename}")
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{filename}"
        print(f"URL da requisição: {url}")
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Content-Type": "application/json"
            },
            json={
                "expiresIn": expires_in
            }
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar URL: {response.text}"
            )
        
        data = response.json()
        signed_url = data["signedURL"]
        
        # Verifica se a URL é relativa e, se for, adiciona a URL base do Supabase
        if signed_url.startswith("/"):
            # Corrige o caminho para incluir /storage/v1/ se necessário
            if signed_url.startswith("/object/sign/"):
                signed_url = f"{settings.SUPABASE_URL}/storage/v1{signed_url}"
            else:
                signed_url = f"{settings.SUPABASE_URL}{signed_url}"
            print(f"URL completa construída: {signed_url}")
        
        return signed_url 