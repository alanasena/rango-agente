"""Testes da API com o modelo falso (não gastam cota)."""

import json

from fastapi.testclient import TestClient

from app.api import app
from app.database import SessionLocal
from app.models import Prato, Restaurante
from tests.modelo_falso import ModeloFalso, chamar, falar


def ids():
    with SessionLocal() as db:
        cantinho = db.query(Restaurante).filter_by(nome="Cantinho Verde").one().id
        moqueca = db.query(Prato).filter_by(nome="Moqueca de banana-da-terra").one().id
    return cantinho, moqueca


def cliente_com_roteiro(roteiro):
    app.state.conversas.clear()
    app.state.fabrica_de_modelo = lambda: ModeloFalso(list(roteiro))
    return TestClient(app)


def ler_eventos(resposta) -> list[dict]:
    return [
        json.loads(linha.removeprefix("data: "))
        for linha in resposta.text.splitlines()
        if linha.startswith("data: ")
    ]


def test_saude():
    assert TestClient(app).get("/saude").json() == {"status": "ok"}


def test_conversa_completa_com_confirmacao():
    cantinho, moqueca = ids()
    itens = [{"prato_id": moqueca, "quantidade": 1}]
    cliente = cliente_com_roteiro([
        chamar("buscar_restaurantes", tem_vegetariano=True),
        chamar("propor_pedido", restaurante_id=cantinho, itens=itens),
        falar("Que tal a moqueca? Clique em Confirmar."),
    ])

    conversa_id = cliente.post("/conversas").json()["conversa_id"]
    resposta = cliente.post(f"/conversas/{conversa_id}/mensagens", json={"texto": "algo vegetariano"})

    assert resposta.headers["content-type"].startswith("text/event-stream")
    eventos = ler_eventos(resposta)
    tipos = [e["tipo"] for e in eventos]
    assert tipos[0] == "passo"
    assert "proposta" in tipos
    assert tipos[-2:] == ["resposta", "fim"]

    confirmado = cliente.post(f"/conversas/{conversa_id}/confirmar")
    assert confirmado.status_code == 200
    assert confirmado.json()["total"] == "R$ 37,90"


def test_confirmar_sem_proposta_da_409():
    cliente = cliente_com_roteiro([falar("Oi!")])
    conversa_id = cliente.post("/conversas").json()["conversa_id"]
    cliente.post(f"/conversas/{conversa_id}/mensagens", json={"texto": "oi"})

    assert cliente.post(f"/conversas/{conversa_id}/confirmar").status_code == 409


def test_conversa_inexistente_da_404():
    cliente = cliente_com_roteiro([])
    assert cliente.post("/conversas/nao-existe/mensagens", json={"texto": "oi"}).status_code == 404


def test_mensagem_vazia_ou_gigante_e_recusada():
    cliente = cliente_com_roteiro([])
    conversa_id = cliente.post("/conversas").json()["conversa_id"]
    url = f"/conversas/{conversa_id}/mensagens"

    assert cliente.post(url, json={"texto": ""}).status_code == 422
    assert cliente.post(url, json={"texto": "a" * 501}).status_code == 422
