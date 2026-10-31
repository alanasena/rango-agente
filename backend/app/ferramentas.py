"""Ferramentas que o agente do Rangô vai poder usar.

Cada função aqui é uma "ferramenta": o Gemini vai decidir QUAL chamar e COM QUAIS
valores, mas quem executa de verdade é o nosso código Python.

Regras importantes:
- Toda ferramenta devolve um dicionário simples (vira JSON para o Gemini ler).
- Em vez de dar erro (exception), a ferramenta devolve {"erro": "..."}.
  Assim o agente lê o problema e consegue explicar ou tentar outra coisa.
- A conta do total é feita SEMPRE aqui, nunca pela IA. IA erra conta.
"""

from app.database import SessionLocal
from app.models import Cupom, Pedido, Prato, Restaurante

QUANTIDADE_MAXIMA_POR_ITEM = 20


def formatar_reais(centavos: int) -> str:
    """3290 -> 'R$ 32,90'"""
    reais = f"{centavos / 100:,.2f}"  # '1,234.50'
    reais = reais.replace(",", "X").replace(".", ",").replace("X", ".")  # '1.234,50'
    return f"R$ {reais}"


# ---------------------------------------------------------------------------
# 1) buscar_restaurantes
# ---------------------------------------------------------------------------
def buscar_restaurantes(
    tipo_cozinha: str | None = None,
    nota_minima: float | None = None,
    tempo_maximo_min: int | None = None,
    tem_vegetariano: bool = False,
    tem_vegano: bool = False,
) -> dict:
    """Busca restaurantes ABERTOS que atendem aos filtros."""
    with SessionLocal() as db:
        consulta = db.query(Restaurante).filter(Restaurante.aberto.is_(True))

        if tipo_cozinha:
            consulta = consulta.filter(Restaurante.tipo_cozinha.ilike(f"%{tipo_cozinha}%"))
        if nota_minima is not None:
            consulta = consulta.filter(Restaurante.nota >= nota_minima)
        if tempo_maximo_min is not None:
            consulta = consulta.filter(Restaurante.tempo_entrega_min <= tempo_maximo_min)
        if tem_vegano:
            consulta = consulta.filter(Restaurante.pratos.any(Prato.vegano.is_(True)))
        elif tem_vegetariano:
            consulta = consulta.filter(Restaurante.pratos.any(Prato.vegetariano.is_(True)))

        restaurantes = consulta.order_by(Restaurante.nota.desc()).all()

        resultado = [
            {
                "id": r.id,
                "nome": r.nome,
                "tipo_cozinha": r.tipo_cozinha,
                "nota": r.nota,
                "tempo_entrega_min": r.tempo_entrega_min,
                "frete": formatar_reais(r.frete_centavos),
                "frete_centavos": r.frete_centavos,
            }
            for r in restaurantes
        ]

    if not resultado:
        return {
            "restaurantes": [],
            "mensagem": "Nenhum restaurante aberto encontrado com esses filtros.",
        }
    return {"restaurantes": resultado}


# ---------------------------------------------------------------------------
# 2) ver_cardapio
# ---------------------------------------------------------------------------
def ver_cardapio(
    restaurante_id: int,
    so_vegetariano: bool = False,
    so_vegano: bool = False,
    preco_maximo_centavos: int | None = None,
) -> dict:
    """Mostra os pratos disponíveis de um restaurante."""
    with SessionLocal() as db:
        restaurante = db.get(Restaurante, restaurante_id)
        if restaurante is None:
            return {"erro": f"Restaurante {restaurante_id} não existe."}
        if not restaurante.aberto:
            return {"erro": f"{restaurante.nome} está fechado agora."}

        pratos = [p for p in restaurante.pratos if p.disponivel]
        if so_vegano:
            pratos = [p for p in pratos if p.vegano]
        elif so_vegetariano:
            pratos = [p for p in pratos if p.vegetariano]
        if preco_maximo_centavos is not None:
            pratos = [p for p in pratos if p.preco_centavos <= preco_maximo_centavos]

        resultado = {
            "restaurante": restaurante.nome,
            "pratos": [
                {
                    "id": p.id,
                    "nome": p.nome,
                    "descricao": p.descricao,
                    "preco": formatar_reais(p.preco_centavos),
                    "preco_centavos": p.preco_centavos,
                    "vegetariano": p.vegetariano,
                    "vegano": p.vegano,
                }
                for p in pratos
            ],
        }

    if not resultado["pratos"]:
        resultado["mensagem"] = "Nenhum prato desse restaurante atende aos filtros."
    return resultado


# ---------------------------------------------------------------------------
# 3) calcular_total
# ---------------------------------------------------------------------------
def calcular_total(
    restaurante_id: int,
    itens: list[dict],
    cupom: str | None = None,
    orcamento_maximo_centavos: int | None = None,
) -> dict:
    """Calcula subtotal + frete - desconto do cupom.

    itens: [{"prato_id": 1, "quantidade": 2}, ...]
    """
    if not itens:
        return {"erro": "O pedido precisa ter pelo menos um item."}

    with SessionLocal() as db:
        restaurante = db.get(Restaurante, restaurante_id)
        if restaurante is None:
            return {"erro": f"Restaurante {restaurante_id} não existe."}
        if not restaurante.aberto:
            return {"erro": f"{restaurante.nome} está fechado agora."}

        linhas = []
        subtotal = 0
        for item in itens:
            prato_id = item.get("prato_id")
            quantidade = item.get("quantidade", 1)

            if not isinstance(quantidade, int) or not 1 <= quantidade <= QUANTIDADE_MAXIMA_POR_ITEM:
                return {"erro": f"Quantidade inválida para o prato {prato_id}: {quantidade}."}

            prato = db.get(Prato, prato_id)
            if prato is None or prato.restaurante_id != restaurante_id:
                return {"erro": f"O prato {prato_id} não é do restaurante {restaurante.nome}."}
            if not prato.disponivel:
                return {"erro": f"{prato.nome} está indisponível."}

            valor = prato.preco_centavos * quantidade
            subtotal += valor
            linhas.append({
                "prato": prato.nome,
                "quantidade": quantidade,
                "valor": formatar_reais(valor),
            })

        frete = restaurante.frete_centavos
        desconto = 0
        avisos = []
        cupom_aplicado = None

        if cupom:
            registro = db.get(Cupom, cupom.strip().upper())
            if registro is None:
                avisos.append(f"Cupom {cupom} não existe.")
            elif not registro.ativo:
                avisos.append(f"Cupom {cupom} não está mais ativo.")
            elif subtotal < registro.pedido_minimo_centavos:
                avisos.append(
                    f"Cupom {cupom} só vale para pedidos a partir de "
                    f"{formatar_reais(registro.pedido_minimo_centavos)}."
                )
            else:
                cupom_aplicado = registro.codigo
                if registro.tipo == "percentual":
                    desconto = subtotal * registro.valor // 100
                elif registro.tipo == "fixo":
                    desconto = min(registro.valor, subtotal)
                elif registro.tipo == "frete_gratis":
                    desconto = frete

    total = subtotal + frete - desconto

    resultado = {
        "restaurante": restaurante.nome,
        "itens": linhas,
        "subtotal": formatar_reais(subtotal),
        "frete": formatar_reais(frete),
        "desconto": formatar_reais(desconto),
        "total": formatar_reais(total),
        "total_centavos": total,
        "cupom_aplicado": cupom_aplicado,
        "avisos": avisos,
    }
    if orcamento_maximo_centavos is not None:
        resultado["dentro_do_orcamento"] = total <= orcamento_maximo_centavos
        if total > orcamento_maximo_centavos:
            falta = total - orcamento_maximo_centavos
            resultado["avisos"].append(
                f"Passa do orçamento em {formatar_reais(falta)}."
            )
    return resultado


# ---------------------------------------------------------------------------
# 4) montar_pedido
# ---------------------------------------------------------------------------
def montar_pedido(
    restaurante_id: int,
    itens: list[dict],
    cupom: str | None = None,
    confirmado_pelo_usuario: bool = False,
) -> dict:
    """Salva o pedido. SÓ funciona se a pessoa confirmou.

    Na etapa 3, quem decide o valor de `confirmado_pelo_usuario` é o NOSSO código
    (quando a pessoa clica em "Confirmar"), e não a IA. Assim a IA nunca consegue
    finalizar um pedido sozinha, mesmo se "quiser".
    """
    if not confirmado_pelo_usuario:
        return {"erro": "Pedido não finalizado: a pessoa ainda não confirmou."}

    # Recalcula aqui mesmo, para não confiar em nenhum valor vindo de fora
    calculo = calcular_total(restaurante_id, itens, cupom)
    if "erro" in calculo:
        return calculo

    with SessionLocal() as db:
        pedido = Pedido(
            restaurante_id=restaurante_id,
            itens=itens,
            cupom=calculo["cupom_aplicado"],
            total_centavos=calculo["total_centavos"],
        )
        db.add(pedido)
        db.commit()
        pedido_id = pedido.id

    return {
        "pedido_id": pedido_id,
        "status": "confirmado",
        "restaurante": calculo["restaurante"],
        "itens": calculo["itens"],
        "total": calculo["total"],
    }
