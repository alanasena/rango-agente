"""Confere se os dados fictícios foram criados direitinho."""

from app.database import SessionLocal
from app.models import Prato, Restaurante


def test_tem_restaurantes_e_pratos():
    with SessionLocal() as db:
        assert db.query(Restaurante).count() == 10
        assert db.query(Prato).count() > 0


def test_todo_prato_vegano_tambem_e_vegetariano():
    with SessionLocal() as db:
        veganos = db.query(Prato).filter(Prato.vegano.is_(True)).all()
        assert all(p.vegetariano for p in veganos)


def test_existe_restaurante_fechado():
    with SessionLocal() as db:
        assert db.query(Restaurante).filter(Restaurante.aberto.is_(False)).count() == 1
