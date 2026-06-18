from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from database import engine, Base
from routers import produtos

# Cria as tabelas ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API E-commerce",
    description="API com arquitetura modular para catálogo de produtos.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas
app.include_router(produtos.router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")