from datetime import datetime
from typing import Optional, Dict
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.core.hashing import verify_password

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)  # Último login do usuário
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.hashed_password)
    
    def update_last_login(self) -> None:
        """
        Atualiza o timestamp do último login.
        """
        self.last_login = datetime.utcnow()
        
    def to_dict(self) -> Dict:
        """
        Converte o usuário em um dicionário para serialização.
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }