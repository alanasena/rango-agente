"""Conexão com o banco de dados.

Lê o endereço do banco da variável DATABASE_URL (arquivo .env).
Se ela não existir, usa um arquivo SQLite local chamado rango.db.
Para trocar por PostgreSQL, basta mudar a DATABASE_URL.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def ajustar_url(url: str) -> str:
    """Serviços como o Neon dão o endereço começando com 'postgresql://' ou 'postgres://'.
    O SQLAlchemy precisa saber qual biblioteca usar, então trocamos para 'postgresql+psycopg://'."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


DATABASE_URL = ajustar_url(os.getenv("DATABASE_URL", "sqlite:///./rango.db"))

if DATABASE_URL.startswith("sqlite"):
    # O SQLite precisa dessa opção para funcionar com o FastAPI (várias requisições ao mesmo tempo)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: confere se a conexão ainda está viva antes de usar
    # (o Neon grátis "desliga" o banco quando fica parado)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Classe base de todas as tabelas."""
