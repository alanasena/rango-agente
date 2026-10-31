"""Testes das ferramentas (ainda sem IA nenhuma)."""

from app.database import SessionLocal
from app.ferramentas import (
    buscar_restaurantes,
    calcular_total,
    formatar_reais,
    montar_pedido,
    ver_cardapio,
)
from app.models import Pedido, Prato, Restaurante


# Ajudantes: acham o id pelo nome, para o teste não depender da ordem do banco
def id_restaurante(nome: str) -> int:
    with SessionLocal() as db:
        return db.query(Restaurante).filter_by(nome=nome).one().id


def id_prato(nome: str) -> int:
    with SessionLocal() as db:
        return db.query(Prato).filter_by(nome=nome).one().id


def nomes(resultado: dict) -> list[str]:
    return [r["nome"] for r in resultado["restaurantes"]]


# --- formatar_reais ---------------------------------------------------------
def test_formatar_reais():
    assert formatar_reais(3290) == "R$ 32,90"
    assert formatar_reais(123450) == "R$ 1.234,50"
    assert formatar_reais(0) == "R$ 0,00"


# --- buscar_restaurantes ----------------------------------------------------
def test_busca_vegetariana_rapida():
    resultado = buscar_restaurantes(tem_vegetariano=True, tempo_maximo_min=40)
    encontrados = nomes(resultado)
    assert "Cantinho Verde" in encontrados
    assert "Raiz Vegana" in encontrados
    assert "Sushi Jangada" not in encontrados  # 50 min, demora demais
    assert all(r["tempo_entrega_min"] <= 40 for r in resultado["restaurantes"])


def test_restaurante_fechado_nunca_aparece():
    assert "Doce Mandacaru" not in nomes(buscar_restaurantes())


def test_busca_sem_resultado_avisa():
    resultado = buscar_restaurantes(tipo_cozinha="mexicana")
    assert resultado["restaurantes"] == []
    assert "Nenhum" in resultado["mensagem"]


def test_busca_ordena_pela_nota():
    notas = [r["nota"] for r in buscar_restaurantes()["restaurantes"]]
    assert notas == sorted(notas, reverse=True)


# --- ver_cardapio -----------------------------------------------------------
def test_cardapio_so_vegano():
    resultado = ver_cardapio(id_restaurante("Cantinho Verde"), so_vegano=True)
    pratos = [p["nome"] for p in resultado["pratos"]]
    assert "Moqueca de banana-da-terra" in pratos
    assert "Lasanha de berinjela" not in pratos  # tem queijo


def test_cardapio_restaurante_fechado_da_erro():
    assert "erro" in ver_cardapio(id_restaurante("Doce Mandacaru"))


def test_cardapio_restaurante_inexistente_da_erro():
    assert "erro" in ver_cardapio(9999)


# --- calcular_total ---------------------------------------------------------
def pedido_moqueca_e_suco():
    return [
        {"prato_id": id_prato("Moqueca de banana-da-terra"), "quantidade": 1},  # 32,90
        {"prato_id": id_prato("Suco de cajá"), "quantidade": 1},  # 8,90
    ]


def test_total_sem_cupom():
    resultado = calcular_total(id_restaurante("Cantinho Verde"), pedido_moqueca_e_suco())
    assert resultado["subtotal"] == "R$ 41,80"
    assert resultado["frete"] == "R$ 5,00"
    assert resultado["total"] == "R$ 46,80"


def test_total_passa_do_orcamento():
    resultado = calcular_total(
        id_restaurante("Cantinho Verde"),
        pedido_moqueca_e_suco(),
        orcamento_maximo_centavos=4000,
    )
    assert resultado["dentro_do_orcamento"] is False
    assert any("orçamento" in aviso for aviso in resultado["avisos"])


def test_cupom_percentual():
    resultado = calcular_total(
        id_restaurante("Cantinho Verde"), pedido_moqueca_e_suco(), cupom="bemvindo10"
    )
    assert resultado["cupom_aplicado"] == "BEMVINDO10"
    assert resultado["desconto"] == "R$ 4,18"
    assert resultado["total"] == "R$ 42,62"


def test_cupom_frete_gratis():
    resultado = calcular_total(
        id_restaurante("Cantinho Verde"), pedido_moqueca_e_suco(), cupom="FRETEGRATIS"
    )
    assert resultado["total"] == "R$ 41,80"


def test_cupom_inativo_nao_da_desconto():
    resultado = calcular_total(
        id_restaurante("Cantinho Verde"), pedido_moqueca_e_suco(), cupom="VENCIDO20"
    )
    assert resultado["cupom_aplicado"] is None
    assert resultado["desconto"] == "R$ 0,00"
    assert resultado["avisos"]


def test_cupom_abaixo_do_minimo():
    itens = [{"prato_id": id_prato("Suco de cajá"), "quantidade": 1}]  # 8,90
    resultado = calcular_total(id_restaurante("Cantinho Verde"), itens, cupom="RANGO5")
    assert resultado["cupom_aplicado"] is None
    assert "a partir de" in resultado["avisos"][0]


def test_prato_de_outro_restaurante_da_erro():
    itens = [{"prato_id": id_prato("Combo 20 peças"), "quantidade": 1}]
    assert "erro" in calcular_total(id_restaurante("Cantinho Verde"), itens)


def test_quantidade_invalida_da_erro():
    itens = [{"prato_id": id_prato("Suco de cajá"), "quantidade": 0}]
    assert "erro" in calcular_total(id_restaurante("Cantinho Verde"), itens)


def test_pedido_vazio_da_erro():
    assert "erro" in calcular_total(id_restaurante("Cantinho Verde"), [])


# --- montar_pedido ----------------------------------------------------------
def contar_pedidos() -> int:
    with SessionLocal() as db:
        return db.query(Pedido).count()


def test_nao_finaliza_sem_confirmacao():
    resultado = montar_pedido(id_restaurante("Cantinho Verde"), pedido_moqueca_e_suco())
    assert "erro" in resultado
    assert contar_pedidos() == 0  # nada foi salvo


def test_finaliza_com_confirmacao():
    resultado = montar_pedido(
        id_restaurante("Cantinho Verde"),
        pedido_moqueca_e_suco(),
        confirmado_pelo_usuario=True,
    )
    assert resultado["status"] == "confirmado"
    assert resultado["total"] == "R$ 46,80"
    assert contar_pedidos() == 1
