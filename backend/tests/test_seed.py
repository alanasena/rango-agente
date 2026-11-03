"""Confere se os dados fictícios foram criados direitinho."""

from app.database import SessionLocal
from app.dados_ficticios import RESTAURANTES
from app.models import Prato, Restaurante


def test_tem_restaurantes_e_pratos():
    with SessionLocal() as db:
        assert db.query(Restaurante).count() == len(RESTAURANTES)
        assert db.query(Prato).count() > 0


def test_todo_prato_vegano_tambem_e_vegetariano():
    with SessionLocal() as db:
        veganos = db.query(Prato).filter(Prato.vegano.is_(True)).all()
        assert all(p.vegetariano for p in veganos)


def test_existe_restaurante_fechado():
    with SessionLocal() as db:
        fechados = db.query(Restaurante).filter(Restaurante.aberto.is_(False)).all()
        assert "Doce Mandacaru" in [r.nome for r in fechados]


def test_nao_tem_comida_mexicana():
    # Um cenário da avaliação testa "comida que não existe no app"
    assert all("mexican" not in r[1] for r in RESTAURANTES)


def test_pratos_usados_nos_testes_tem_nome_unico():
    with SessionLocal() as db:
        for nome in ["Moqueca de banana-da-terra", "Suco de cajá", "Combo 20 peças"]:
            assert db.query(Prato).filter_by(nome=nome).count() == 1
