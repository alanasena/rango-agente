"""Roda todos os cenários com o Gemini de verdade e gera um relatório.

Como rodar (dentro da pasta backend, com o .env preenchido):
    python -m avaliacao.rodar

O relatório vai para avaliacao/RESULTADO.md (bom para colocar no README).
Gasta umas 40 chamadas da cota do Gemini, então não rode toda hora.
"""

import os

# Usa um banco só para a avaliação (não mexe no rango.db). Precisa vir antes dos imports do app.
os.environ["DATABASE_URL"] = "sqlite:///./avaliacao.db"

import sys  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

from app.agente import Agente  # noqa: E402
from app.seed import popular_banco  # noqa: E402
from avaliacao.cenarios import CENARIOS, Execucao  # noqa: E402

PAUSA_ENTRE_CENARIOS_SEG = 8  # dá um respiro para a cota por minuto do Gemini
ARQUIVO_RESULTADO = Path(__file__).parent / "RESULTADO.md"


def rodar_cenario(cenario, fabrica_de_modelo) -> tuple[Execucao, list[str]]:
    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):  # esconde a mensagem do seed
        popular_banco()  # banco limpo para cada cenário

    execucao = Execucao(agente=Agente(fabrica_de_modelo()))
    for mensagem in cenario.mensagens:
        execucao.eventos_por_mensagem.append(list(execucao.agente.responder(mensagem)))
    return execucao, cenario.conferir(execucao)


def main(fabrica_de_modelo=None, pausa: float = PAUSA_ENTRE_CENARIOS_SEG) -> int:
    if fabrica_de_modelo is None:
        from app.modelo_gemini import ModeloGemini

        fabrica_de_modelo = ModeloGemini

    linhas = []
    aprovados = 0

    for i, cenario in enumerate(CENARIOS, start=1):
        print(f"[{i}/{len(CENARIOS)}] {cenario.nome}...", end=" ", flush=True)
        execucao, problemas = rodar_cenario(cenario, fabrica_de_modelo)
        passou = not problemas
        aprovados += passou
        print("✅" if passou else "❌ " + "; ".join(problemas))

        linhas.append(
            f"| {cenario.nome} | {'✅' if passou else '❌'} | "
            f"{' → '.join(execucao.ferramentas_usadas) or '(nenhuma)'} | "
            f"{'; '.join(problemas) or '-'} |"
        )
        if i < len(CENARIOS):
            time.sleep(pausa)

    relatorio = "\n".join([
        "# Avaliação do agente com o Gemini",
        "",
        f"Rodado em {datetime.now():%d/%m/%Y %H:%M}. Resultado: **{aprovados} de {len(CENARIOS)}** cenários aprovados.",
        "",
        "| Cenário | Passou? | Ferramentas usadas | Problemas |",
        "|---|---|---|---|",
        *linhas,
        "",
    ])
    ARQUIVO_RESULTADO.write_text(relatorio, encoding="utf-8")
    print(f"\n{aprovados}/{len(CENARIOS)} aprovados. Relatório salvo em {ARQUIVO_RESULTADO}")
    return 0 if aprovados == len(CENARIOS) else 1


if __name__ == "__main__":
    sys.exit(main())
