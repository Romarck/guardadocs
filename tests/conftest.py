import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.db.session import get_db
from app.main import app

# Configurar o arquivo .env.test para os testes
os.environ["ENV_FILE"] = ".env.test"

# Criar um banco de dados SQLite em memória para os testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Criar as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Criar uma nova sessão para o teste
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Remover as tabelas após o teste
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    # Sobrescrever a dependência do banco de dados
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Criar um cliente de teste
    test_client = TestClient(app)
    yield test_client
    
    # Limpar as dependências após o teste
    app.dependency_overrides.clear() 