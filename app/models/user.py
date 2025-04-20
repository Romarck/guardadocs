from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.core.hashing import verify_password

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)  # Pode ser NULL para usuários do Google
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_google_user = Column(Boolean, default=False)  # Indica se o usuário foi criado via Google
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.hashed_password) 