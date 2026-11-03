"""Ligação com o Gemini de verdade (usa a biblioteca google-genai).

Esta classe guarda o histórico da conversa e conversa com a API.
Ela segue o mesmo "contrato" (ModeloIA) do agente.py.
"""

import logging
import os
import re
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from app.agente import (
    DECLARACOES_FERRAMENTAS,
    ChamadaFerramenta,
    ModeloIndisponivel,
    RespostaModelo,
)
from app.prompts import INSTRUCOES_DO_AGENTE

load_dotenv()

# O nome do modelo fica no .env. "gemini-flash-latest" aponta sempre para o Flash mais novo.
MODELO_PADRAO = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
# Modelo reserva: usado quando o principal está lotado
MODELO_RESERVA = os.getenv("GEMINI_MODEL_RESERVA", "gemini-flash-lite-latest")

# Quanto o modelo "pensa" antes de responder. "low" deixa as respostas bem mais rápidas e
# basta para escolher restaurante e prato. Opções: low, medium, high (deixe vazio para o padrão).
NIVEL_PENSAMENTO = os.getenv("GEMINI_PENSAMENTO", "low")

# Tempo máximo esperando o Gemini responder. Sem isso, se o servidor travar, o agente
# fica "Pensando..." para sempre.
LIMITE_DE_ESPERA_SEG = float(os.getenv("GEMINI_TIMEOUT_SEG", "30"))

log = logging.getLogger("rango.gemini")


class EsperaEsgotada(Exception):
    """O Gemini não respondeu dentro do limite de tempo."""


# Modelos "de castigo": quando um modelo responde que a cota acabou (429), anotamos até
# quando não vale a pena tentar ele de novo. Fica fora da classe porque a cota é do
# projeto inteiro, não de uma conversa só.
MODELOS_EM_PAUSA: dict[str, float] = {}
PAUSA_COTA_DIARIA_SEG = 30 * 60  # cota do dia acabou: só tenta de novo daqui a 30 min
PAUSA_PADRAO_SEG = 60  # cota por minuto: espera 1 min


def pausar_modelo(modelo: str, erro: errors.APIError) -> None:
    texto = str(erro)
    if "PerDay" in texto:
        segundos = PAUSA_COTA_DIARIA_SEG
    else:
        achou = re.search(r"retryDelay'?:\s*'?(\d+)", texto)
        segundos = int(achou.group(1)) + 1 if achou else PAUSA_PADRAO_SEG
    MODELOS_EM_PAUSA[modelo] = time.monotonic() + segundos
    log.warning("Pausando %s por %d min (cota esgotada).", modelo, max(1, round(segundos / 60)))


def esta_em_pausa(modelo: str) -> bool:
    return time.monotonic() < MODELOS_EM_PAUSA.get(modelo, 0)

# Erros que valem tentar de novo: 429 = muitos pedidos, 500/503 = servidor com problema
CODIGOS_TEMPORARIOS = {429, 500, 503}
TENTATIVAS = 2  # no modelo principal; depois vai para o reserva
ESPERA_INICIAL_SEG = 2


class ModeloGemini:
    def __init__(
        self,
        api_key: str | None = None,
        modelo: str = MODELO_PADRAO,
        modelo_reserva: str | None = MODELO_RESERVA,
        espera_inicial_seg: float = ESPERA_INICIAL_SEG,
        nivel_pensamento: str | None = NIVEL_PENSAMENTO,
    ):
        self.modelo_reserva = modelo_reserva
        self.espera_inicial_seg = espera_inicial_seg
        self.nivel_pensamento = nivel_pensamento
        chave = api_key or os.getenv("GEMINI_API_KEY")
        if not chave:
            raise RuntimeError("Coloque sua GEMINI_API_KEY no arquivo .env")

        self.cliente = genai.Client(
            api_key=chave,
            http_options=types.HttpOptions(timeout=int(LIMITE_DE_ESPERA_SEG * 1000)),  # em milissegundos
        )
        self.modelo = modelo
        self.historico: list[types.Content] = []

        self.ferramentas = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=d["name"],
                    description=d["description"],
                    parameters_json_schema=d["parameters"],
                )
                for d in DECLARACOES_FERRAMENTAS
            ]
        )

    def _config(self, so_texto: bool, modelo: str = "") -> types.GenerateContentConfig:
        opcoes = dict(
            system_instruction=INSTRUCOES_DO_AGENTE,
            tools=[self.ferramentas],
            temperature=0.2,  # mais previsível
            # Desliga o modo automático: quem roda as ferramentas é o NOSSO agente
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        # Os modelos "lite" já respondem sem pensar; ligar o ajuste neles deixaria mais LENTO
        if self.nivel_pensamento and "lite" not in modelo:
            opcoes["thinking_config"] = types.ThinkingConfig(thinking_level=self.nivel_pensamento)
        if so_texto:
            opcoes["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="NONE")
            )
        return types.GenerateContentConfig(**opcoes)

    # --- contrato ModeloIA -------------------------------------------------
    def enviar_mensagem(self, texto: str) -> RespostaModelo:
        self.historico.append(types.Content(role="user", parts=[types.Part.from_text(text=texto)]))
        return self._gerar(so_texto=False)

    def enviar_resultados(self, resultados, forcar_texto: bool = False) -> RespostaModelo:
        partes = [types.Part.from_function_response(name=nome, response=res) for nome, res in resultados]
        if forcar_texto:
            partes.append(types.Part.from_text(
                text="[Aviso do sistema] Limite de passos atingido. Responda agora, só com texto."
            ))
        self.historico.append(types.Content(role="user", parts=partes))
        return self._gerar(so_texto=forcar_texto)

    def adicionar_contexto(self, texto: str) -> None:
        self.historico.append(types.Content(role="user", parts=[types.Part.from_text(text=texto)]))

    # --- chamada à API ----------------------------------------------------
    def _pedir(self, modelo: str, so_texto: bool):
        try:
            return self.cliente.models.generate_content(
                model=modelo, contents=self.historico, config=self._config(so_texto, modelo)
            )
        except httpx.TimeoutException as erro:
            raise EsperaEsgotada() from erro
        except errors.APIError as erro:
            # Se o modelo não aceitar o ajuste de "pensamento", desliga e tenta de novo
            if erro.code == 400 and self.nivel_pensamento and "think" in str(erro).lower():
                log.warning("Modelo %s não aceita thinking_level; seguindo sem ele.", modelo)
                self.nivel_pensamento = None
                return self._pedir(modelo, so_texto)
            raise

    def _tentar(self, modelo: str, so_texto: bool, tentativa: int):
        """Uma tentativa. Devolve a resposta, ou None se valer a pena tentar de novo."""
        log.info("Chamando %s (tentativa %d)...", modelo, tentativa)
        inicio = time.perf_counter()
        try:
            resposta = self._pedir(modelo, so_texto)
            log.info("%s respondeu em %.1fs", modelo, time.perf_counter() - inicio)
            return resposta
        except EsperaEsgotada:
            log.warning("%s não respondeu em %.0fs.", modelo, LIMITE_DE_ESPERA_SEG)
        except errors.APIError as erro:
            if erro.code not in CODIGOS_TEMPORARIOS:
                raise  # erro de verdade (ex.: chave errada): melhor mostrar
            motivo = "cota do plano grátis esgotada" if erro.code == 429 else "servidor do Google lotado"
            log.warning("%s respondeu %d (%s).", modelo, erro.code, motivo)
            if erro.code == 429:
                pausar_modelo(modelo, erro)
        return None

    def _chamar_api(self, so_texto: bool):
        """Tenta o modelo principal (até 2 vezes). Se ele estiver com a cota esgotada ou
        com problema, vai para o modelo reserva."""
        espera = self.espera_inicial_seg
        for tentativa in range(1, TENTATIVAS + 1):
            if esta_em_pausa(self.modelo):
                log.info("Pulando %s: cota esgotada, usando o reserva.", self.modelo)
                break
            resposta = self._tentar(self.modelo, so_texto, tentativa)
            if resposta is not None:
                return resposta
            if tentativa < TENTATIVAS and not esta_em_pausa(self.modelo):
                time.sleep(espera)
                espera *= 2

        reserva = self.modelo_reserva
        if reserva and reserva != self.modelo and not esta_em_pausa(reserva):
            resposta = self._tentar(reserva, so_texto, 1)
            if resposta is not None:
                return resposta

        log.error("Nenhum modelo respondeu. Avisando a pessoa para tentar mais tarde.")
        raise ModeloIndisponivel()

    def _gerar(self, so_texto: bool) -> RespostaModelo:
        resposta = self._chamar_api(so_texto)

        conteudo = resposta.candidates[0].content if resposta.candidates else None
        if conteudo is not None:
            # Guarda a resposta inteira (inclusive partes internas do "pensamento" do modelo)
            self.historico.append(conteudo)

        chamadas = [
            ChamadaFerramenta(nome=c.name, argumentos=dict(c.args or {}))
            for c in (resposta.function_calls or [])
        ]
        texto = "".join(
            p.text for p in (conteudo.parts or []) if p.text and not p.thought
        ) if conteudo else ""
        return RespostaModelo(texto=texto, chamadas=chamadas)
