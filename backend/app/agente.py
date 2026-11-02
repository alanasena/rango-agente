"""O agente do Rangô.

Como ele funciona (o ciclo "pensar -> usar ferramenta -> ver resultado"):

    pessoa escreve
         |
         v
    Gemini PENSA e responde de dois jeitos possíveis:
      a) "quero usar a ferramenta X com estes valores"  -> nosso código EXECUTA X
         e devolve o resultado pro Gemini, que pensa de novo (volta pro começo)
      b) um texto final                               -> mostramos pra pessoa e acabou

Para não entrar em loop, existe um LIMITE DE PASSOS. Se o limite chegar, mandamos
os últimos resultados e obrigamos o Gemini a responder só com texto.

Segurança: a IA NÃO tem a ferramenta de finalizar. Ela só consegue PROPOR um pedido
(propor_pedido). Quem finaliza é o método confirmar_pedido(), chamado quando a pessoa
clica no botão "Confirmar" na tela. Assim, nem por engano a IA finaliza sozinha.
"""

from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol

from app import ferramentas

LIMITE_DE_PASSOS = 8


# ---------------------------------------------------------------------------
# O "contrato" do modelo de IA
# ---------------------------------------------------------------------------
@dataclass
class ChamadaFerramenta:
    nome: str
    argumentos: dict[str, Any]


@dataclass
class RespostaModelo:
    texto: str = ""
    chamadas: list[ChamadaFerramenta] = field(default_factory=list)


class ModeloIndisponivel(Exception):
    """O modelo de IA não respondeu (servidor lotado, cota acabou, sem internet...)."""


class ModeloIA(Protocol):
    """Qualquer modelo que siga este contrato funciona com o agente.

    O Gemini de verdade está em modelo_gemini.py. Nos testes usamos um modelo
    falso que segue o mesmo contrato, para não gastar cota.
    """

    def enviar_mensagem(self, texto: str) -> RespostaModelo: ...

    def enviar_resultados(
        self, resultados: list[tuple[str, dict]], forcar_texto: bool = False
    ) -> RespostaModelo: ...

    def adicionar_contexto(self, texto: str) -> None: ...


# ---------------------------------------------------------------------------
# As ferramentas que o Gemini enxerga (nome, para que serve e o que recebe)
# ---------------------------------------------------------------------------
_ITENS_SCHEMA = {
    "type": "array",
    "description": "Pratos do pedido.",
    "items": {
        "type": "object",
        "properties": {
            "prato_id": {"type": "integer"},
            "quantidade": {"type": "integer"},
        },
        "required": ["prato_id", "quantidade"],
    },
}

DECLARACOES_FERRAMENTAS = [
    {
        "name": "buscar_restaurantes",
        "description": "Busca restaurantes abertos. Todos os filtros são opcionais.",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo_cozinha": {
                    "type": "string",
                    "description": "Ex.: vegetariana, vegana, nordestina, japonesa, pizza, "
                    "hamburguer, lanches, caseira, italiana.",
                },
                "nota_minima": {"type": "number", "description": "De 0 a 5."},
                "tempo_maximo_min": {"type": "integer", "description": "Tempo máximo de entrega em minutos."},
                "tem_vegetariano": {"type": "boolean", "description": "Só restaurantes com prato vegetariano."},
                "tem_vegano": {"type": "boolean", "description": "Só restaurantes com prato vegano."},
            },
        },
    },
    {
        "name": "ver_cardapio",
        "description": "Mostra os pratos disponíveis de um restaurante.",
        "parameters": {
            "type": "object",
            "properties": {
                "restaurante_id": {"type": "integer"},
                "so_vegetariano": {"type": "boolean"},
                "so_vegano": {"type": "boolean"},
                "preco_maximo_reais": {"type": "number", "description": "Preço máximo de cada prato, em reais."},
            },
            "required": ["restaurante_id"],
        },
    },
    {
        "name": "calcular_total",
        "description": "Calcula o total do pedido (pratos + frete - cupom) e diz se cabe no orçamento.",
        "parameters": {
            "type": "object",
            "properties": {
                "restaurante_id": {"type": "integer"},
                "itens": _ITENS_SCHEMA,
                "cupom": {"type": "string"},
                "orcamento_maximo_reais": {"type": "number"},
            },
            "required": ["restaurante_id", "itens"],
        },
    },
    {
        "name": "propor_pedido",
        "description": "Mostra o pedido para a pessoa confirmar. NÃO finaliza: "
        "só a pessoa finaliza clicando em Confirmar.",
        "parameters": {
            "type": "object",
            "properties": {
                "restaurante_id": {"type": "integer"},
                "itens": _ITENS_SCHEMA,
                "cupom": {"type": "string"},
                "orcamento_maximo_reais": {
                    "type": "number",
                    "description": "Orçamento que a pessoa deu, se ela deu algum.",
                },
            },
            "required": ["restaurante_id", "itens"],
        },
    },
]

# Texto que aparece na tela enquanto cada ferramenta roda
DESCRICAO_DOS_PASSOS = {
    "buscar_restaurantes": "Buscando restaurantes...",
    "ver_cardapio": "Olhando o cardápio...",
    "calcular_total": "Calculando o total...",
    "propor_pedido": "Montando a sugestão de pedido...",
}


# ---------------------------------------------------------------------------
# Eventos: o que o agente vai "contando" enquanto trabalha (a tela usa isso)
# ---------------------------------------------------------------------------
@dataclass
class Evento:
    tipo: str  # "passo", "resultado", "proposta", "resposta"
    texto: str = ""
    ferramenta: str | None = None
    dados: dict | None = None

    def para_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in (None, "")}


# ---------------------------------------------------------------------------
# Ajudantes
# ---------------------------------------------------------------------------
def _reais_para_centavos(valor: Any) -> int | None:
    if valor is None:
        return None
    return round(float(valor) * 100)


def _inteiro(valor: Any) -> Any:
    """O Gemini às vezes manda 2.0 em vez de 2. Aqui a gente arruma."""
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor


def _normalizar_itens(itens: Any) -> list[dict]:
    if not isinstance(itens, list):
        return []
    return [
        {"prato_id": _inteiro(i.get("prato_id")), "quantidade": _inteiro(i.get("quantidade", 1))}
        for i in itens
        if isinstance(i, dict)
    ]


# ---------------------------------------------------------------------------
# O agente
# ---------------------------------------------------------------------------
class Agente:
    def __init__(self, modelo: ModeloIA, limite_de_passos: int = LIMITE_DE_PASSOS):
        self.modelo = modelo
        self.limite_de_passos = limite_de_passos
        self.pedido_pendente: dict | None = None

    # --- o ciclo principal -------------------------------------------------
    def responder(self, mensagem: str) -> Iterator[Evento]:
        # Uma mensagem nova cancela a proposta anterior: só vale confirmar a mais recente.
        self.pedido_pendente = None
        try:
            yield from self._ciclo(mensagem)
        except ModeloIndisponivel:
            # Em vez de o app quebrar, a pessoa recebe um aviso e pode tentar de novo
            yield Evento(
                "resposta",
                texto="O Gemini está sobrecarregado ou sem cota agora. "
                "Espera um pouquinho e manda a mensagem de novo, por favor.",
            )

    def _ciclo(self, mensagem: str) -> Iterator[Evento]:
        resposta = self.modelo.enviar_mensagem(mensagem)
        passos = 0

        while resposta.chamadas:
            resultados = []
            for chamada in resposta.chamadas:
                passos += 1
                yield Evento(
                    "passo",
                    texto=DESCRICAO_DOS_PASSOS.get(chamada.nome, f"Usando {chamada.nome}..."),
                    ferramenta=chamada.nome,
                )
                resultado = self._executar(chamada)
                yield Evento("resultado", ferramenta=chamada.nome, dados=resultado)
                if chamada.nome == "propor_pedido" and "erro" not in resultado:
                    yield Evento("proposta", dados=self.pedido_pendente["resumo"])
                resultados.append((chamada.nome, resultado))

            chegou_no_limite = passos >= self.limite_de_passos
            resposta = self.modelo.enviar_resultados(resultados, forcar_texto=chegou_no_limite)
            if chegou_no_limite:
                break

        texto = resposta.texto.strip() or (
            "Desculpa, não consegui resolver isso agora. Pode tentar explicar de outro jeito?"
        )
        yield Evento("resposta", texto=texto)

    # --- botão "Confirmar" -------------------------------------------------
    def confirmar_pedido(self) -> dict:
        """Chamado pela TELA quando a pessoa clica em Confirmar. A IA não chama isto."""
        if self.pedido_pendente is None:
            return {"erro": "Não há nenhum pedido esperando confirmação."}

        pendente = self.pedido_pendente
        resultado = ferramentas.montar_pedido(
            pendente["restaurante_id"],
            pendente["itens"],
            pendente["cupom"],
            confirmado_pelo_usuario=True,
        )
        if "erro" not in resultado:
            self.pedido_pendente = None
            self.modelo.adicionar_contexto(
                f"[Aviso do sistema] A pessoa clicou em Confirmar. "
                f"Pedido #{resultado['pedido_id']} finalizado, total {resultado['total']}."
            )
        return resultado

    # --- executa uma ferramenta pedida pelo Gemini -------------------------
    def _executar(self, chamada: ChamadaFerramenta) -> dict:
        args = chamada.argumentos or {}
        try:
            if chamada.nome == "buscar_restaurantes":
                return ferramentas.buscar_restaurantes(
                    tipo_cozinha=args.get("tipo_cozinha"),
                    nota_minima=args.get("nota_minima"),
                    tempo_maximo_min=_inteiro(args.get("tempo_maximo_min")),
                    tem_vegetariano=bool(args.get("tem_vegetariano", False)),
                    tem_vegano=bool(args.get("tem_vegano", False)),
                )
            if chamada.nome == "ver_cardapio":
                return ferramentas.ver_cardapio(
                    _inteiro(args["restaurante_id"]),
                    so_vegetariano=bool(args.get("so_vegetariano", False)),
                    so_vegano=bool(args.get("so_vegano", False)),
                    preco_maximo_centavos=_reais_para_centavos(args.get("preco_maximo_reais")),
                )
            if chamada.nome == "calcular_total":
                return ferramentas.calcular_total(
                    _inteiro(args["restaurante_id"]),
                    _normalizar_itens(args.get("itens")),
                    cupom=args.get("cupom") or None,
                    orcamento_maximo_centavos=_reais_para_centavos(args.get("orcamento_maximo_reais")),
                )
            if chamada.nome == "propor_pedido":
                return self._propor_pedido(args)
            return {"erro": f"A ferramenta '{chamada.nome}' não existe."}
        except (KeyError, TypeError, ValueError) as problema:
            return {"erro": f"Valores inválidos para {chamada.nome}: {problema}"}

    def _propor_pedido(self, args: dict) -> dict:
        restaurante_id = _inteiro(args["restaurante_id"])
        itens = _normalizar_itens(args.get("itens"))
        cupom = args.get("cupom") or None
        orcamento = _reais_para_centavos(args.get("orcamento_maximo_reais"))

        calculo = ferramentas.calcular_total(restaurante_id, itens, cupom, orcamento)
        if "erro" in calculo:
            return calculo
        # Trava de segurança no CÓDIGO, não só nas instruções da IA
        if calculo.get("dentro_do_orcamento") is False:
            return {"erro": f"Não dá para propor: o total {calculo['total']} passa do orçamento."}

        self.pedido_pendente = {
            "restaurante_id": restaurante_id,
            "itens": itens,
            "cupom": calculo["cupom_aplicado"],
            "resumo": calculo,
        }
        return {
            "status": "aguardando_confirmacao",
            "resumo": calculo,
            "instrucao": "Mostre o resumo e peça para a pessoa clicar em Confirmar.",
        }
