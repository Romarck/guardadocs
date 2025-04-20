from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_url: str
    file_size: int
    content_type: str

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    pass

class DocumentInDBBase(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class Document(DocumentInDBBase):
    pass

class DocumentInDB(DocumentInDBBase):
    pass 