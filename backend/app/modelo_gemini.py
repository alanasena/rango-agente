"""Ligação com o Gemini de verdade (usa a biblioteca google-genai).

Esta classe guarda o histórico da conversa e conversa com a API.
Ela segue o mesmo "contrato" (ModeloIA) do agente.py.
"""

import logging
import os
import time

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

log = logging.getLogger("rango.gemini")

# Erros que valem tentar de novo: 429 = muitos pedidos, 500/503 = servidor com problema
CODIGOS_TEMPORARIOS = {429, 500, 503}
TENTATIVAS = 3
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

        self.cliente = genai.Client(api_key=chave)
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

    def _config(self, so_texto: bool) -> types.GenerateContentConfig:
        opcoes = dict(
            system_instruction=INSTRUCOES_DO_AGENTE,
            tools=[self.ferramentas],
            temperature=0.2,  # mais previsível
            # Desliga o modo automático: quem roda as ferramentas é o NOSSO agente
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        if self.nivel_pensamento:
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
                model=modelo, contents=self.historico, config=self._config(so_texto)
            )
        except errors.APIError as erro:
            # Se o modelo não aceitar o ajuste de "pensamento", desliga e tenta de novo
            if erro.code == 400 and self.nivel_pensamento and "think" in str(erro).lower():
                log.warning("Modelo %s não aceita thinking_level; seguindo sem ele.", modelo)
                self.nivel_pensamento = None
                return self.cliente.models.generate_content(
                    model=modelo, contents=self.historico, config=self._config(so_texto)
                )
            raise

    def _chamar_api(self, so_texto: bool):
        """Tenta algumas vezes, esperando cada vez mais (2s, 4s, 8s...).
        Se o modelo principal continuar lotado, tenta uma vez com o modelo reserva."""
        espera = self.espera_inicial_seg
        for tentativa in range(TENTATIVAS):
            try:
                return self._pedir(self.modelo, so_texto)
            except errors.APIError as erro:
                if erro.code not in CODIGOS_TEMPORARIOS:
                    raise  # erro de verdade (ex.: chave errada): melhor mostrar
                if tentativa < TENTATIVAS - 1:
                    time.sleep(espera)
                    espera *= 2

        if self.modelo_reserva and self.modelo_reserva != self.modelo:
            try:
                return self._pedir(self.modelo_reserva, so_texto)
            except errors.APIError as erro:
                if erro.code not in CODIGOS_TEMPORARIOS:
                    raise

        raise ModeloIndisponivel()

    def _gerar(self, so_texto: bool) -> RespostaModelo:
        inicio = time.perf_counter()
        resposta = self._chamar_api(so_texto)
        log.info("Gemini respondeu em %.1fs", time.perf_counter() - inicio)

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
