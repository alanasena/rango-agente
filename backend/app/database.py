"""Conexão com o banco de dados.

Lê o endereço do banco da variável DATABASE_URL (arquivo .env).
Se ela não existir, usa um arquivo SQLite local chamado rango.db.
Para trocar por PostgreSQL depois, basta mudar a DATABASE_URL.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rango.db")

# O SQLite precisa dessa opção para funcionar com o FastAPI (várias requisições ao mesmo tempo)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Classe base de todas as tabelas."""
