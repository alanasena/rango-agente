"""Configuração dos testes.

Os testes usam um banco SEPARADO (teste.db), para não mexer no rango.db
que você usa no dia a dia. Esta linha precisa vir antes de importar o app.
"""

import os

# Dá para testar no PostgreSQL também: defina TEST_DATABASE_URL
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///./teste.db")

import pytest  # noqa: E402

from app.seed import popular_banco  # noqa: E402


@pytest.fixture(autouse=True)
def banco_limpo():
    """Recria o banco antes de CADA teste, para um teste não atrapalhar o outro."""
    popular_banco()
