from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base, User
from app.core.hashing import get_password_hash

def init_db():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Create admin user if not exists
    admin = db.query(User).filter(User.email == "admin@guarda.com").first()
    if not admin:
        admin = User(
            email="admin@guarda.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()

if __name__ == "__main__":
    init_db() 