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
    from app import modelo_gemini

    modelo_gemini.MODELOS_EM_PAUSA.clear()
    modelo = ModeloGemini(api_key="falsa", modelo="principal", modelo_reserva="reserva",
                          espera_inicial_seg=0)
    modelo.cliente = ClienteFalso(respostas)
    return modelo


def test_tenta_de_novo_quando_servidor_lotado():
    modelo = criar_modelo([erro_503(), resposta_texto("Oi!")])
    assert modelo.enviar_mensagem("oi").texto == "Oi!"
    assert modelo.cliente.modelos_usados == ["principal", "principal"]


def test_usa_modelo_reserva_se_principal_continua_lotado():
    modelo = criar_modelo([erro_503(), erro_503(), resposta_texto("Oi da reserva!")])
    assert modelo.enviar_mensagem("oi").texto == "Oi da reserva!"
    assert modelo.cliente.modelos_usados[-1] == "reserva"


def test_avisa_quando_nada_funciona():
    modelo = criar_modelo([erro_503()] * 3)
    with pytest.raises(ModeloIndisponivel):
        modelo.enviar_mensagem("oi")


def test_agente_nao_quebra_quando_gemini_cai():
    modelo = criar_modelo([erro_503()] * 3)
    eventos = list(Agente(modelo).responder("quero pizza"))
    assert eventos[-1].tipo == "resposta"
    assert "sobrecarregado" in eventos[-1].texto


def erro_400_pensamento():
    return errors.ClientError(400, {"error": {"code": 400, "message": "thinking_level is not supported", "status": "INVALID_ARGUMENT"}})


def test_pede_para_pensar_pouco():
    modelo = criar_modelo([resposta_texto("Oi!")])
    config = modelo._config(so_texto=False, modelo="gemini-flash-latest")
    assert config.thinking_config.thinking_level.value.lower() == "low"


def test_modelo_lite_nao_recebe_ajuste_de_pensamento():
    modelo = criar_modelo([resposta_texto("Oi!")])
    assert modelo._config(so_texto=False, modelo="gemini-flash-lite-latest").thinking_config is None


def test_se_modelo_nao_aceita_ajuste_de_pensamento_segue_sem_ele():
    modelo = criar_modelo([erro_400_pensamento(), resposta_texto("Oi!")])
    assert modelo.enviar_mensagem("oi").texto == "Oi!"
    assert modelo.nivel_pensamento is None
    assert modelo._config(so_texto=False).thinking_config is None


def test_se_o_gemini_travar_desiste_e_usa_o_reserva():
    import httpx

    modelo = criar_modelo([httpx.ReadTimeout("demorou"), httpx.ReadTimeout("demorou"), resposta_texto("Oi da reserva!")])
    assert modelo.enviar_mensagem("oi").texto == "Oi da reserva!"
    assert modelo.cliente.modelos_usados == ["principal", "principal", "reserva"]


def erro_429_diario():
    return errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED",
        "message": "Quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier"}})


def test_cota_esgotada_vai_direto_pro_reserva_nas_proximas():
    modelo = criar_modelo([erro_429_diario(), resposta_texto("1"), resposta_texto("2")])
    assert modelo.enviar_mensagem("oi").texto == "1"
    assert modelo.cliente.modelos_usados == ["principal", "reserva"]  # não insiste no principal

    assert modelo.enviar_mensagem("de novo").texto == "2"
    assert modelo.cliente.modelos_usados == ["principal", "reserva", "reserva"]  # pula direto
