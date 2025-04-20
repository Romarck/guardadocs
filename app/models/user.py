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
    full_name = Column(String, index=True)
    hashed_password = Column(String, nullable=True)  # Pode ser NULL para usuários do Google
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_google_user = Column(Boolean, default=False)  # Indica se o usuário foi criado via Google
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    google_id = Column(String, unique=True, nullable=True)
    profile_picture = Column(String, nullable=True)  # URL da foto do perfil do Google
    last_login = Column(DateTime, nullable=True)  # Último login do usuário
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        if not self.hashed_password:
            return False
        return verify_password(password, self.hashed_password)
    
    @classmethod
    def from_google_data(cls, google_data: Dict) -> "User":
        """
        Cria uma instância de User a partir dos dados do Google OAuth.
        """
        return cls(
            email=google_data.get("email"),
            full_name=google_data.get("name"),
            is_google_user=True,
            google_id=google_data.get("sub"),
            profile_picture=google_data.get("picture"),
            is_active=True
        )
    
    def update_from_google_data(self, google_data: Dict) -> None:
        """
        Atualiza os dados do usuário com informações do Google OAuth.
        """
        self.full_name = google_data.get("name", self.full_name)
        self.profile_picture = google_data.get("picture", self.profile_picture)
        self.last_login = datetime.utcnow()
        
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
            "is_google_user": self.is_google_user,
            "profile_picture": self.profile_picture,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }