from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import User

def test_register_user(client: TestClient, db_session: Session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "hashed_password" not in data

def test_login_user(client: TestClient, db_session: Session):
    # Criar um usuário para teste
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    # Tentar fazer login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer" 