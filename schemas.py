from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome do produto não pode ser vazio")
    preco: float = Field(..., gt=0, description="Preço deve ser maior que zero")
    estoque: int = Field(default=0, ge=0)
    ativo: bool = Field(default=True)

class ProdutoResponse(BaseModel):
    id: int
    nome: str
    preco: float
    estoque: int
    ativo: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)