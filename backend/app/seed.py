"""Preenche o banco com dados FICTÍCIOS do Rangô.

Todos os restaurantes, pratos, preços, fretes e cupons são inventados.
Rodar de novo apaga tudo e recria do zero (bom para testes).

Como rodar (dentro da pasta backend):
    python -m app.seed
"""

from app.database import Base, SessionLocal, engine
from app.models import Cupom, Prato, Restaurante

# (nome, tipo_cozinha, nota, tempo_entrega_min, frete_centavos, aberto, pratos)
# pratos: (nome, descricao, preco_centavos, vegetariano, vegano)
RESTAURANTES = [
    ("Cantinho Verde", "vegetariana", 4.7, 30, 500, True, [
        ("Moqueca de banana-da-terra", "Com arroz e farofa de dendê", 3290, True, True),
        ("Lasanha de berinjela", "Molho de tomate, queijo e manjericão", 2990, True, False),
        ("Bowl de grão-de-bico", "Arroz integral, legumes assados e tahine", 2690, True, True),
        ("Suco de cajá", "500 ml", 890, True, True),
    ]),
    ("Raiz Vegana", "vegana", 4.8, 40, 400, True, [
        ("Hambúrguer de feijão", "Pão australiano, alface e maionese de castanha", 2790, True, True),
        ("Strogonoff de cogumelos", "Com arroz e batata palha", 3190, True, True),
        ("Brownie de cacau", "Sem leite e sem ovo", 1290, True, True),
    ]),
    ("Brasa do Sertão", "nordestina", 4.5, 45, 700, True, [
        ("Baião de dois com carne de sol", "Serve 1 pessoa", 3890, False, False),
        ("Paçoca de carne de sol", "Com banana e arroz", 3490, False, False),
        ("Escondidinho de macaxeira com queijo coalho", "Versão vegetariana", 2890, True, False),
        ("Cuscuz recheado", "Com ovo e queijo", 1890, True, False),
    ]),
    ("Sushi Jangada", "japonesa", 4.6, 50, 990, True, [
        ("Combo 20 peças", "Salmão, kani e skin", 5990, False, False),
        ("Temaki de salmão", "Com cream cheese", 2690, False, False),
        ("Hot roll vegetariano", "Pepino, cenoura e manga (10 peças)", 2490, True, True),
        ("Yakisoba de legumes", "Individual", 3290, True, True),
    ]),
    ("Forno da Vila", "pizza", 4.3, 35, 600, True, [
        ("Pizza marguerita média", "Molho, mussarela e manjericão", 3990, True, False),
        ("Pizza calabresa média", "Calabresa e cebola", 4290, False, False),
        ("Pizza de legumes média", "Sem queijo, massa sem ovo", 4190, True, True),
        ("Refrigerante lata", "350 ml", 650, True, True),
    ]),
    ("Burguer do Açude", "hamburguer", 4.2, 25, 550, True, [
        ("X-Açude", "Hambúrguer bovino, queijo e bacon", 2890, False, False),
        ("Burguer de falafel", "Com molho de iogurte", 2690, True, False),
        ("Batata frita", "Porção média", 1490, True, True),
    ]),
    ("Tapiocaria da Praça", "lanches", 4.4, 20, 300, True, [
        ("Tapioca de queijo coalho", "Com manteiga da terra", 1290, True, False),
        ("Tapioca de frango com catupiry", "Bem recheada", 1590, False, False),
        ("Tapioca de banana com canela", "Doce", 1190, True, True),
    ]),
    ("Panela de Barro", "caseira", 4.1, 30, 0, True, [
        ("Marmita de frango grelhado", "Arroz, feijão, salada e farofa", 2190, False, False),
        ("Marmita de panqueca de legumes", "Arroz, feijão e salada", 1990, True, False),
        ("Marmita de feijoada", "Sábado especial", 2590, False, False),
    ]),
    ("Trattoria Carnaúba", "italiana", 4.5, 55, 800, True, [
        ("Espaguete ao pesto", "Manjericão, castanha e azeite", 3690, True, True),
        ("Nhoque à bolonhesa", "Molho de carne", 3990, False, False),
        ("Risoto de abóbora", "Com parmesão", 4190, True, False),
    ]),
    # Fechado de propósito: o agente nunca deve sugerir pedido daqui
    ("Doce Mandacaru", "sobremesas", 4.9, 35, 450, False, [
        ("Bolo de rolo", "Fatia", 990, True, False),
        ("Pudim de leite", "Fatia", 1090, True, False),
    ]),
]

# (codigo, tipo, valor, pedido_minimo_centavos, ativo)
CUPONS = [
    ("BEMVINDO10", "percentual", 10, 3000, True),  # 10% em pedidos a partir de R$ 30
    ("RANGO5", "fixo", 500, 2500, True),  # R$ 5 off a partir de R$ 25
    ("FRETEGRATIS", "frete_gratis", 0, 2000, True),  # frete grátis a partir de R$ 20
    ("VENCIDO20", "percentual", 20, 0, False),  # inativo: o agente deve recusar
]


def popular_banco() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        for nome, tipo, nota, tempo, frete, aberto, pratos in RESTAURANTES:
            restaurante = Restaurante(
                nome=nome,
                tipo_cozinha=tipo,
                nota=nota,
                tempo_entrega_min=tempo,
                frete_centavos=frete,
                aberto=aberto,
            )
            for p_nome, desc, preco, veg, vegano in pratos:
                restaurante.pratos.append(
                    Prato(
                        nome=p_nome,
                        descricao=desc,
                        preco_centavos=preco,
                        vegetariano=veg,
                        vegano=vegano,
                    )
                )
            db.add(restaurante)

        for codigo, tipo, valor, minimo, ativo in CUPONS:
            db.add(Cupom(codigo=codigo, tipo=tipo, valor=valor,
                         pedido_minimo_centavos=minimo, ativo=ativo))

        db.commit()

        total_rest = db.query(Restaurante).count()
        total_pratos = db.query(Prato).count()
        total_cupons = db.query(Cupom).count()

    print(f"Banco pronto: {total_rest} restaurantes, {total_pratos} pratos, {total_cupons} cupons.")


if __name__ == "__main__":
    popular_banco()
