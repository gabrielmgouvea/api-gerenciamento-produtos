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

@router.get("/", response_model=List[schemas.ProdutoResponse], status_code=status.HTTP_200_OK)
def listar_produtos(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    return db.query(models.Produto).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=schemas.ProdutoResponse, status_code=status.HTTP_200_OK)
def buscar_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    db.delete(produto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)