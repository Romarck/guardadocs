from app.db.session import SessionLocal
from app.models import User
from app.core.password import get_password_hash

db = SessionLocal()
user = User(
    email='test@example.com',
    full_name='Test User',
    hashed_password=get_password_hash('test123'),
    is_active=True
)
db.add(user)
db.commit()
print('Usuário criado com sucesso!') 