from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Document, User
from app.schemas import document
from app.services.storage_service import StorageService
from app.api.deps import get_current_user
import uuid
import os

router = APIRouter(prefix="/documents", tags=["documents"])
storage_service = StorageService()

@router.post("/", response_model=document.Document)
async def create_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
) -> Any:
    """
    Create new document.
    """
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file
    file_url = await storage_service.save_file(file.file, unique_filename)
    
    # Create document record
    db_document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_url=file_url,
        file_size=file.size,
        content_type=file.content_type,
        user_id=current_user.id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.get("/", response_model=List[document.Document])
async def read_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve documents.
    """
    documents = db.query(Document).filter(Document.user_id == current_user.id).offset(skip).limit(limit).all()
    return documents

@router.get("/{document_id}", response_model=document.Document)
async def read_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get document by ID.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

@router.put("/{document_id}", response_model=document.Document)
async def update_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    document_in: document.DocumentUpdate,
) -> Any:
    """
    Update document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    for field, value in document_in.dict(exclude_unset=True).items():
        setattr(document, field, value)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

@router.delete("/{document_id}", response_model=document.Document)
async def delete_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete document.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    # Delete file from storage
    await storage_service.delete_file(document.filename)
    # Delete from database
    db.delete(document)
    db.commit()
    return document 