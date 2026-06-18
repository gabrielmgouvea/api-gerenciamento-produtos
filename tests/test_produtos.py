import pytest
from fastapi import status
from models import Produto

# 1. Listar produtos quando o banco está vazio
def test_listar_produtos_banco_vazio(client):
    response = client.get("/produtos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

# 2. Criar produto e verificar persistência no banco
def test_criar_produto_persistencia(client, db_session):
    payload = {"nome": "Teclado Mecânico", "preco": 350.0, "estoque": 15, "ativo": True}
    response = client.post("/produtos/", json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    dados = response.json()
    assert dados["nome"] == "Teclado Mecânico"
    assert "id" in dados

    # Verifica direto no banco via SQLAlchemy se ele foi salvo
    produto_db = db_session.query(Produto).filter(Produto.id == dados["id"]).first()
    assert produto_db is not None
    assert produto_db.preco == 350.0

# 3. Criar produto e verificar que aparece na listagem
def test_criar_produto_aparece_listagem(client):
    client.post("/produtos/", json={"nome": "Mouse Gamer", "preco": 120.50})
    
    response = client.get("/produtos/")
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert len(dados) == 1
    assert dados[0]["nome"] == "Mouse Gamer"

# 4. Buscar produto por id — caso de sucesso (Usa a fixture)
def test_buscar_produto_sucesso(client, produto_existente):
    response = client.get(f"/produtos/{produto_existente.id}")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nome"] == "Notebook Dell"

# 5. Buscar produto com id inexistente — deve retornar 404
def test_buscar_produto_inexistente(client):
    response = client.get("/produtos/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Produto não encontrado"

# 6. Deletar produto — deve retornar 204
def test_deletar_produto_sucesso(client, produto_existente):
    response = client.delete(f"/produtos/{produto_existente.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

# 7. Deletar produto e confirmar remoção com GET subsequente
def test_deletar_produto_confirmar_remocao(client, produto_existente):
    client.delete(f"/produtos/{produto_existente.id}")
    
    response = client.get(f"/produtos/{produto_existente.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# 8. Deletar produto inexistente — deve retornar 404
def test_deletar_produto_inexistente(client):
    response = client.delete("/produtos/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# 9. Pelo menos 1 teste parametrizado cobrindo payloads inválidos (status 422)
@pytest.mark.parametrize("payload_invalido", [
    {"nome": "", "preco": 100.0},          # Nome vazio (erro min_length)
    {"nome": "Monitor", "preco": -50.0},   # Preço negativo
    {"nome": "Cadeira", "preco": 0},       # Preço zero (erro gt=0)
    {"preco": 150.0},                      # Faltando campo obrigatório: nome
    {"nome": "Mesa"}                       # Faltando campo obrigatório: preco
])
def test_criar_produto_payloads_invalidos(client, payload_invalido):
    response = client.post("/produtos/", json=payload_invalido)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# 10. Pelo menos 1 teste que valide que o banco está isolado entre execuções
def test_validar_isolamento_do_banco(client):
    """
    Se o banco não fosse dropado/recriado a cada teste pela fixture (isolamento), 
    ele estaria sujo com o 'Teclado Mecânico' ou 'Mouse Gamer' dos testes anteriores.
    """
    response = client.get("/produtos/")
    assert response.status_code == status.HTTP_200_OK
    # Valida que nenhum lixo dos testes de cima sobrou!
    assert response.json() == []