import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import User, Document
from app.core.security import get_password_hash, create_access_token

def test_create_document(client: TestClient, db_session: Session):
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    user_id = user.id

    # Create access token
    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create test file
    test_file_path = "test_file.txt"
    with open(test_file_path, "w") as f:
        f.write("Test file content")

    # Send file using multipart/form-data
    with open(test_file_path, "rb") as f:
        response = client.post(
            "/api/v1/documents/",
            headers=headers,
            files={"file": ("test_file.txt", f, "text/plain")}
        )

    # Clean up test file
    os.remove(test_file_path)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"].endswith(".txt")
    assert data["original_filename"] == "test_file.txt"
    assert data["content_type"] == "text/plain"
    assert data["file_size"] > 0
    assert data["user_id"] == user_id

def test_get_document(client: TestClient, db_session: Session):
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create test document
    document = Document(
        filename="unique_test.txt",
        original_filename="test.txt",
        file_url="https://example.com/test.txt",
        file_size=1024,
        content_type="text/plain",
        user_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    # Create access token
    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get document
    response = client.get(
        f"/api/v1/documents/{document.id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document.id
    assert data["filename"] == document.filename
    assert data["original_filename"] == document.original_filename
    assert data["file_url"] == document.file_url
    assert data["file_size"] == document.file_size
    assert data["content_type"] == document.content_type
    assert data["user_id"] == user.id

def test_list_documents(client: TestClient, db_session: Session):
    # Criar um usuário de teste
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    # Criar documentos de teste
    documents = [
        Document(
            title=f"Test Document {i}",
            description=f"This is test document description {i}",
            filename=f"test{i}.txt",
            file_path=f"/path/to/test{i}.txt",
            file_size=1024,
            mime_type="text/plain",
            owner_id=user.id
        )
        for i in range(3)
    ]
    for doc in documents:
        db_session.add(doc)
    db_session.commit()
    
    # Fazer login para obter o token
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Listar os documentos
    response = client.get(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for i, doc in enumerate(data):
        assert doc["title"] == f"Test Document {i}"
        assert doc["description"] == f"This is test document description {i}"
        assert doc["filename"] == f"test{i}.txt"
        assert doc["file_path"] == f"/path/to/test{i}.txt"
        assert doc["file_size"] == 1024
        assert doc["mime_type"] == "text/plain"
        assert doc["owner_id"] == user.id 