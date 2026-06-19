from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.post("/", response_model=schemas.ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(produto: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = models.Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

# ATUALIZADO: Filtros inteligentes na listagem
@router.get("/", response_model=List[schemas.ProdutoResponse], status_code=status.HTTP_200_OK)
def listar_produtos(
    skip: int = Query(0), 
    limit: int = Query(100),
    nome: str | None = Query(None, description="Filtra produtos pelo nome (parcial)"),
    ativo: bool | None = Query(None, description="Filtra produtos por status de atividade"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Produto)
    
    if nome:
        query = query.filter(models.Produto.nome.ilike(f"%{nome}%"))
    if ativo is not None:
        query = query.filter(models.Produto.ativo == ativo)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{id}", response_model=schemas.ProdutoResponse, status_code=status.HTTP_200_OK)
def buscar_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

# NOVO: Rota de atualização (Diferencial Sênior)
@router.patch("/{id}", response_model=schemas.ProdutoResponse, status_code=status.HTTP_200_OK)
def atualizar_produto(id: int, produto_atualizado: schemas.ProdutoUpdate, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Atualiza apenas os campos enviados no payload
    update_data = produto_atualizado.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(produto, key, value)
        
    db.commit()
    db.refresh(produto)
    return produto

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    db.delete(produto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)