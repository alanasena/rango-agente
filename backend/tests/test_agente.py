"""Testes do agente com o modelo falso (não gastam cota do Gemini)."""

from app.agente import Agente
from app.database import SessionLocal
from app.models import Pedido, Prato, Restaurante
from tests.modelo_falso import ModeloFalso, chamar, falar


def id_restaurante(nome: str) -> int:
    with SessionLocal() as db:
        return db.query(Restaurante).filter_by(nome=nome).one().id


def id_prato(nome: str) -> int:
    with SessionLocal() as db:
        return db.query(Prato).filter_by(nome=nome).one().id


def contar_pedidos() -> int:
    with SessionLocal() as db:
        return db.query(Pedido).count()


def tipos(eventos) -> list[str]:
    return [e.tipo for e in eventos]


def itens_moqueca():
    return [{"prato_id": id_prato("Moqueca de banana-da-terra"), "quantidade": 1}]


# ---------------------------------------------------------------------------
def test_fluxo_completo_propoe_mas_nao_finaliza_sozinho():
    cantinho = id_restaurante("Cantinho Verde")
    modelo = ModeloFalso([
        chamar("buscar_restaurantes", tem_vegetariano=True, tempo_maximo_min=40),
        chamar("ver_cardapio", restaurante_id=cantinho, so_vegetariano=True),
        chamar("calcular_total", restaurante_id=cantinho, itens=itens_moqueca(), orcamento_maximo_reais=40),
        chamar("propor_pedido", restaurante_id=cantinho, itens=itens_moqueca(), orcamento_maximo_reais=40),
        falar("Sugiro a moqueca do Cantinho Verde por R$ 37,90. Clique em Confirmar!"),
    ])
    agente = Agente(modelo)

    eventos = list(agente.responder("jantar vegetariano até R$ 40 em menos de 40 min"))

    passos = [e.ferramenta for e in eventos if e.tipo == "passo"]
    assert passos == ["buscar_restaurantes", "ver_cardapio", "calcular_total", "propor_pedido"]
    assert "proposta" in tipos(eventos)
    assert eventos[-1].tipo == "resposta"
    assert contar_pedidos() == 0  # ninguém clicou em Confirmar ainda

    resultado = agente.confirmar_pedido()
    assert resultado["status"] == "confirmado"
    assert resultado["total"] == "R$ 37,90"  # 32,90 + 5,00 de frete
    assert contar_pedidos() == 1
    assert modelo.contextos  # o modelo fica sabendo que a pessoa confirmou


def test_limite_de_passos_evita_loop():
    # Modelo "teimoso": pede a mesma ferramenta pra sempre
    modelo = ModeloFalso([chamar("buscar_restaurantes")], repetir_ultima=True)
    agente = Agente(modelo, limite_de_passos=3)

    eventos = list(agente.responder("oi"))

    assert tipos(eventos).count("passo") == 3
    assert modelo.foi_forcado_a_falar
    assert eventos[-1].tipo == "resposta"


def test_trava_de_orcamento_no_codigo():
    # Mesmo se a IA tentar propor acima do orçamento, o código bloqueia
    cantinho = id_restaurante("Cantinho Verde")
    modelo = ModeloFalso([
        chamar("propor_pedido", restaurante_id=cantinho, itens=itens_moqueca(), orcamento_maximo_reais=20),
        falar("Não achei nada dentro de R$ 20."),
    ])
    agente = Agente(modelo)

    eventos = list(agente.responder("até 20 reais"))

    assert "proposta" not in tipos(eventos)
    assert "erro" in modelo.resultados_recebidos[0][1]
    assert agente.confirmar_pedido().get("erro")  # não há nada para confirmar


def test_ia_nao_tem_ferramenta_de_finalizar():
    modelo = ModeloFalso([
        chamar("montar_pedido", restaurante_id=1, itens=[], confirmado_pelo_usuario=True),
        falar("Ops."),
    ])
    list(Agente(modelo).responder("finaliza aí"))

    assert "não existe" in modelo.resultados_recebidos[0][1]["erro"]
    assert contar_pedidos() == 0


def test_mudar_de_ideia_cancela_proposta_antiga():
    cantinho = id_restaurante("Cantinho Verde")
    modelo = ModeloFalso([
        chamar("propor_pedido", restaurante_id=cantinho, itens=itens_moqueca()),
        falar("Que tal a moqueca?"),
        falar("Beleza, vamos procurar pizza então."),  # resposta da 2ª mensagem
    ])
    agente = Agente(modelo)

    list(agente.responder("algo vegetariano"))
    assert agente.pedido_pendente is not None

    list(agente.responder("na verdade quero pizza"))
    assert agente.pedido_pendente is None
    assert "erro" in agente.confirmar_pedido()
    assert contar_pedidos() == 0


def test_numeros_quebrados_do_gemini_sao_arrumados():
    # O Gemini às vezes manda 1.0 em vez de 1
    cantinho = id_restaurante("Cantinho Verde")
    itens = [{"prato_id": float(id_prato("Suco de cajá")), "quantidade": 2.0}]
    modelo = ModeloFalso([
        chamar("calcular_total", restaurante_id=float(cantinho), itens=itens),
        falar("Deu R$ 22,80."),
    ])
    list(Agente(modelo).responder("dois sucos"))

    assert modelo.resultados_recebidos[0][1]["total"] == "R$ 22,80"


def test_argumento_faltando_vira_erro_e_nao_quebra():
    modelo = ModeloFalso([chamar("ver_cardapio"), falar("Qual restaurante?")])
    eventos = list(Agente(modelo).responder("cardápio"))

    assert "erro" in modelo.resultados_recebidos[0][1]
    assert eventos[-1].texto == "Qual restaurante?"
