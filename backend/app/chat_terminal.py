"""Converse com o agente pelo terminal (usa o Gemini de verdade).

Como rodar (dentro da pasta backend, com o .env preenchido):
    python -m app.chat_terminal

Digite "confirmar" para clicar no botão Confirmar, ou "sair" para encerrar.
"""

from app.agente import Agente
from app.modelo_gemini import ModeloGemini


def main() -> None:
    agente = Agente(ModeloGemini())
    print("Rangô 🍽️  — diga o que você quer comer (ou 'sair')\n")

    while True:
        mensagem = input("Você: ").strip()
        if mensagem.lower() in {"sair", "exit"}:
            break
        if not mensagem:
            continue

        if mensagem.lower() == "confirmar":
            resultado = agente.confirmar_pedido()
            if "erro" in resultado:
                print(f"   ⚠️  {resultado['erro']}\n")
            else:
                print(f"   ✅ Pedido #{resultado['pedido_id']} confirmado! Total: {resultado['total']}\n")
            continue

        for evento in agente.responder(mensagem):
            if evento.tipo == "passo":
                print(f"   ⏳ {evento.texto}")
            elif evento.tipo == "proposta":
                print(f"   🧾 Pedido sugerido: {evento.dados['total']} (digite 'confirmar' para finalizar)")
            elif evento.tipo == "resposta":
                print(f"\nRangô: {evento.texto}\n")


if __name__ == "__main__":
    main()
