import pytest
from fastapi import status
from sqlalchemy.exc import IntegrityError
from models import Produto

def test_deve_retornar_lista_vazia_quando_banco_nao_tem_registros(client):
    """Garante que a listagem inicial não traz dados residuais de outras execuções."""
    response = client.get("/produtos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_deve_criar_produto_via_api_e_persistir_no_banco(client, db_session):
    """Verifica se o fluxo de criação reflete fisicamente no banco de dados."""
    payload = {"nome": "Teclado Mecânico", "preco": 350.0, "estoque": 15, "ativo": True}
    response = client.post("/produtos/", json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    dados = response.json()
    assert dados["nome"] == "Teclado Mecânico"

    produto_db = db_session.query(Produto).filter(Produto.id == dados["id"]).first()
    assert produto_db is not None
    assert produto_db.preco == 350.0

def test_deve_listar_produtos_recem_criados(client):
    """Valida se o endpoint GET recupera os dados inseridos na mesma sessão."""
    client.post("/produtos/", json={"nome": "Mouse Gamer", "preco": 120.50})
    
    response = client.get("/produtos/")
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert len(dados) == 1
    assert dados[0]["nome"] == "Mouse Gamer"

def test_deve_encontrar_produto_existente_pelo_id(client, produto_existente):
    """Busca direta por ID (Happy Path)."""
    response = client.get(f"/produtos/{produto_existente.id}")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nome"] == "Notebook Dell"

def test_deve_retornar_404_ao_buscar_id_inexistente(client):
    """Valida o tratamento de exceção para recursos não encontrados."""
    response = client.get("/produtos/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Produto não encontrado"

def test_deve_permitir_atualizar_estoque_do_produto_via_patch(client, produto_existente):
    """Garante que o PATCH atualiza apenas campos específicos, mantendo o resto."""
    payload = {"estoque": 50}  # Atualizando apenas um campo
    response = client.patch(f"/produtos/{produto_existente.id}", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["estoque"] == 50
    assert dados["nome"] == "Notebook Dell"  # Campo antigo deve se manter intacto

def test_deve_excluir_produto_com_sucesso(client, produto_existente):
    """Valida a deleção física e o status HTTP 204."""
    response = client.delete(f"/produtos/{produto_existente.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_nao_deve_encontrar_produto_apos_exclusao(client, produto_existente):
    """Garante que a deleção removeu permanentemente o registro da base."""
    client.delete(f"/produtos/{produto_existente.id}")
    response = client.get(f"/produtos/{produto_existente.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_deve_retornar_404_ao_tentar_excluir_id_inexistente(client):
    """Valida o idempotency da deleção ou tratamento de erro adequado."""
    response = client.delete("/produtos/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.parametrize("payload_invalido", [
    {"nome": "", "preco": 100.0},
    {"nome": "Monitor", "preco": -50.0},
    {"nome": "Cadeira", "preco": 0},
    {"preco": 150.0},
    {"nome": "Mesa"}
])
def test_deve_barrar_payloads_invalidos_na_criacao(client, payload_invalido):
    """Valida se o Pydantic intercepta esquemas incorretos retornando 422."""
    response = client.post("/produtos/", json=payload_invalido)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_deve_lancar_erro_de_integridade_ao_burlar_constraint_do_banco(db_session):
    """
    PROVA TÉCNICA: Valida que testes contra banco de dados real 
    (PostgreSQL) pegam erros que passariam em banco SQLite em memória.
    Testa se o CheckConstraint do banco barra preços negativos mesmo sem o FastAPI.
    """
    produto_invalido = Produto(nome="Hack Db", preco=-10.0, estoque=5, ativo=True)
    db_session.add(produto_invalido)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_deve_garantir_isolamento_absoluto_entre_testes(client):
    """
    Se a suíte não limpar a base (Setup/Teardown com fixtures), 
    este teste falhará por encontrar lixo deixado pelas funções anteriores.
    """
    response = client.get("/produtos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []