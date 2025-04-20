from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import User

def test_create_user(client: TestClient, db_session: Session):
    # Criar um usuário de teste
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "is_active" in data
    assert "is_superuser" in data

def test_get_user(client: TestClient, db_session: Session):
    # Criar um usuário de teste
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    # Fazer login para obter o token
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Obter o usuário
    response = client.get(
        f"/api/v1/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert data["id"] == user.id 