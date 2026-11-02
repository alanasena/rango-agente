"""Testa a ligação com o Gemini SEM internet: trocamos o cliente por um falso."""

import pytest
from google.genai import errors, types

from app.agente import Agente, ModeloIndisponivel
from app.modelo_gemini import ModeloGemini


def erro_503():
    return errors.ServerError(503, {"error": {"code": 503, "message": "lotado", "status": "UNAVAILABLE"}})


def resposta_texto(texto: str):
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role="model", parts=[types.Part(text=texto)])
    )])


class ClienteFalso:
    """Devolve (ou levanta) cada item da lista, um por chamada, e anota o modelo usado."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.modelos_usados = []
        self.models = self

    def generate_content(self, model, contents, config):
        self.modelos_usados.append(model)
        item = self.respostas.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def criar_modelo(respostas):
    modelo = ModeloGemini(api_key="falsa", modelo="principal", modelo_reserva="reserva",
                          espera_inicial_seg=0)
    modelo.cliente = ClienteFalso(respostas)
    return modelo


def test_tenta_de_novo_quando_servidor_lotado():
    modelo = criar_modelo([erro_503(), resposta_texto("Oi!")])
    assert modelo.enviar_mensagem("oi").texto == "Oi!"
    assert modelo.cliente.modelos_usados == ["principal", "principal"]


def test_usa_modelo_reserva_se_principal_continua_lotado():
    modelo = criar_modelo([erro_503(), erro_503(), erro_503(), resposta_texto("Oi da reserva!")])
    assert modelo.enviar_mensagem("oi").texto == "Oi da reserva!"
    assert modelo.cliente.modelos_usados[-1] == "reserva"


def test_avisa_quando_nada_funciona():
    modelo = criar_modelo([erro_503()] * 4)
    with pytest.raises(ModeloIndisponivel):
        modelo.enviar_mensagem("oi")


def test_agente_nao_quebra_quando_gemini_cai():
    modelo = criar_modelo([erro_503()] * 4)
    eventos = list(Agente(modelo).responder("quero pizza"))
    assert eventos[-1].tipo == "resposta"
    assert "sobrecarregado" in eventos[-1].texto
