from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)  # Nome do documento (opcional)
    description = Column(String, nullable=True)  # Descrição do documento (opcional)
    original_filename = Column(String, nullable=False)  # Nome original do arquivo
    storage_filename = Column(String, nullable=False, unique=True)  # Nome do arquivo no storage
    file_size = Column(Integer, nullable=False)  # Tamanho em bytes
    content_type = Column(String, nullable=False)  # Tipo MIME
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="documents") 