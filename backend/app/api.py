"""API do Rangô (FastAPI).

Rotas:
    GET  /saude                         -> confere se a API está no ar
    POST /conversas                     -> começa uma conversa nova
    POST /conversas/{id}/mensagens      -> manda uma mensagem; os passos do agente
                                           chegam AO VIVO (um por um), via SSE
    POST /conversas/{id}/confirmar      -> o botão "Confirmar" da tela

Como rodar (dentro da pasta backend):
    uvicorn app.api:app --reload

Depois abra http://localhost:8000/docs para testar as rotas pelo navegador.

O que é SSE (Server-Sent Events)? É um jeito de o servidor ir mandando pedacinhos da
resposta enquanto trabalha, em vez de mandar tudo só no final. É isso que faz a tela
mostrar "Buscando restaurantes..." na hora em que acontece.
"""

import json
import os
import time
import uuid
from collections import OrderedDict, defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agente import Agente
from app.database import Base, SessionLocal, engine
from app.models import Restaurante
from app.seed import popular_banco

MAXIMO_DE_CONVERSAS = 200  # guardadas na memória; as mais antigas saem primeiro
TAMANHO_MAXIMO_MENSAGEM = 500  # evita textos gigantes gastando a cota do Gemini
# Quando o site estiver público, isso impede que uma pessoa sozinha gaste toda a sua cota
LIMITE_MENSAGENS_POR_HORA = int(os.getenv("LIMITE_MENSAGENS_POR_HORA", "30"))


def criar_modelo_gemini():
    from app.modelo_gemini import ModeloGemini  # só importa quando precisa

    return ModeloGemini()


@asynccontextmanager
async def ao_iniciar(app: FastAPI):
    """Na primeira vez que a API sobe, cria as tabelas e os dados fictícios."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        banco_vazio = db.query(Restaurante).count() == 0
    if banco_vazio:
        popular_banco()
    yield


app = FastAPI(title="Rangô API", version="0.1.0", lifespan=ao_iniciar)

# Quem pode chamar a API pelo navegador (o front-end)
origens = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origens],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Trocável nos testes (lá usamos o modelo falso)
app.state.fabrica_de_modelo = criar_modelo_gemini
app.state.conversas = OrderedDict()  # conversa_id -> Agente
app.state.mensagens_por_ip = defaultdict(deque)  # ip -> horários das últimas mensagens


# ---------------------------------------------------------------------------
class NovaMensagem(BaseModel):
    texto: str = Field(min_length=1, max_length=TAMANHO_MAXIMO_MENSAGEM)


def pegar_agente(conversa_id: str) -> Agente:
    agente = app.state.conversas.get(conversa_id)
    if agente is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada. Comece uma nova.")
    return agente


def ip_de_quem_chamou(request: Request) -> str:
    # Na hospedagem, o IP real vem no fim do cabeçalho X-Forwarded-For
    encaminhado = request.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[-1].strip()
    return request.client.host if request.client else "desconhecido"


def checar_limite(request: Request) -> None:
    agora = time.monotonic()
    horarios = app.state.mensagens_por_ip[ip_de_quem_chamou(request)]
    while horarios and agora - horarios[0] > 3600:
        horarios.popleft()
    if len(horarios) >= LIMITE_MENSAGENS_POR_HORA:
        raise HTTPException(
            status_code=429,
            detail="Você mandou muitas mensagens em pouco tempo. Tenta de novo daqui a pouco.",
        )
    horarios.append(agora)


def formato_sse(dados: dict) -> str:
    return f"data: {json.dumps(dados, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.post("/conversas", status_code=201)
def nova_conversa():
    conversas = app.state.conversas
    if len(conversas) >= MAXIMO_DE_CONVERSAS:
        conversas.popitem(last=False)  # tira a mais antiga

    conversa_id = uuid.uuid4().hex
    conversas[conversa_id] = Agente(app.state.fabrica_de_modelo())
    return {"conversa_id": conversa_id}


@app.post("/conversas/{conversa_id}/mensagens")
def enviar_mensagem(conversa_id: str, mensagem: NovaMensagem, request: Request):
    agente = pegar_agente(conversa_id)
    checar_limite(request)

    def transmitir():
        for evento in agente.responder(mensagem.texto.strip()):
            yield formato_sse(evento.para_dict())
        yield formato_sse({"tipo": "fim"})

    return StreamingResponse(
        transmitir(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/conversas/{conversa_id}/confirmar")
def confirmar(conversa_id: str):
    resultado = pegar_agente(conversa_id).confirmar_pedido()
    if "erro" in resultado:
        raise HTTPException(status_code=409, detail=resultado["erro"])
    return resultado
