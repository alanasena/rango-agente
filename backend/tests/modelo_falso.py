"""Um "Gemini de mentira" para os testes.

Em vez de pensar, ele devolve respostas que a gente escreveu antes (um roteiro).
Assim testamos o AGENTE (o ciclo, o limite, as travas) sem gastar cota.
"""

from app.agente import ChamadaFerramenta, RespostaModelo


def chamar(nome: str, **argumentos) -> RespostaModelo:
    """Atalho: resposta em que o modelo pede para usar uma ferramenta."""
    return RespostaModelo(chamadas=[ChamadaFerramenta(nome, argumentos)])


def falar(texto: str) -> RespostaModelo:
    """Atalho: resposta em que o modelo só fala."""
    return RespostaModelo(texto=texto)


class ModeloFalso:
    def __init__(self, roteiro: list[RespostaModelo], repetir_ultima: bool = False):
        self.roteiro = list(roteiro)
        self.repetir_ultima = repetir_ultima
        self.resultados_recebidos: list[tuple[str, dict]] = []
        self.contextos: list[str] = []
        self.foi_forcado_a_falar = False

    def _proxima(self) -> RespostaModelo:
        if self.repetir_ultima and len(self.roteiro) == 1:
            return self.roteiro[0]
        return self.roteiro.pop(0)

    def enviar_mensagem(self, texto: str) -> RespostaModelo:
        return self._proxima()

    def enviar_resultados(self, resultados, forcar_texto: bool = False) -> RespostaModelo:
        self.resultados_recebidos.extend(resultados)
        if forcar_texto:
            self.foi_forcado_a_falar = True
            return falar("Não consegui terminar, pode reformular?")
        return self._proxima()

    def adicionar_contexto(self, texto: str) -> None:
        self.contextos.append(texto)
