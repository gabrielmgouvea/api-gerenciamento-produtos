import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
from models import Produto

# Banco exclusivo para testes na porta 5433
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/produtos_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Cria as tabelas limpas antes de CADA teste e as destrói depois."""
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Substitui a injeção de dependência do banco real pelo de teste."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def produto_existente(db_session):
    """Fixture auxiliar para testes de busca e deleção."""
    produto = Produto(nome="Notebook Dell", preco=3500.00, estoque=10, ativo=True)
    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)
    return produto