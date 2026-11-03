"""Restaurantes, pratos e cupons FICTÍCIOS do Rangô.

Tudo aqui é inventado: nomes, pratos, preços, fretes e tempos de entrega.
Para acrescentar um restaurante, copie uma linha e mude os valores.

Formato de cada restaurante:
    (nome, tipo_cozinha, nota, tempo_entrega_min, frete_centavos, aberto, pratos)
Formato de cada prato:
    (nome, descricao, preco_centavos, vegetariano, vegano)

Regras para não quebrar os testes:
- Os primeiros 10 restaurantes são usados pelos testes: não mude os nomes nem os pratos deles.
- Não crie restaurante de comida MEXICANA: um cenário testa "comida que não existe no app".
- Todo prato vegano também precisa ser vegetariano (True, True).
"""

RESTAURANTES = [
    # ---- os 10 originais (usados pelos testes) ----
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

    # ---- nordestina ----
    ("Casa do Baião", "nordestina", 4.6, 40, 600, True, [
        ("Baião de dois tradicional", "Com queijo coalho e nata", 2990, True, False),
        ("Carne de sol na nata", "Com macaxeira frita", 4490, False, False),
        ("Galinha caipira guisada", "Com pirão e arroz", 3790, False, False),
        ("Feijão verde com jerimum", "Com arroz e farofa", 2490, True, True),
    ]),
    ("Sabor do Jaguaribe", "nordestina", 4.3, 50, 800, True, [
        ("Panelada", "Serve 1 pessoa", 3290, False, False),
        ("Sarrabulho", "Com arroz e farofa", 2990, False, False),
        ("Cuscuz com carne de sol desfiada", "Com manteiga da terra", 2290, False, False),
    ]),
    ("Pirão da Vovó", "nordestina", 4.7, 35, 500, True, [
        ("Peixe ao molho de coco", "Com pirão e arroz", 4290, False, False),
        ("Arrumadinho de feijão verde", "Com charque e vinagrete", 2790, False, False),
        ("Macaxeira com queijo coalho", "Porção individual", 1890, True, False),
    ]),

    # ---- japonesa e chinesa ----
    ("Temaki da Lagoa", "japonesa", 4.4, 30, 600, True, [
        ("Temaki de salmão grelhado", "Com cebolinha", 2490, False, False),
        ("Temaki de manga com pepino", "Com gergelim", 1990, True, True),
        ("Uramaki filadélfia", "8 peças", 2890, False, False),
    ]),
    ("Kaiten Iracema", "japonesa", 4.8, 60, 1200, True, [
        ("Barca 40 peças", "Serve 2 pessoas", 11990, False, False),
        ("Sashimi de atum", "10 fatias", 4890, False, False),
        ("Missoshiru", "Sopa de missô com tofu", 1290, True, True),
    ]),
    ("Dragão do Centro", "chinesa", 4.0, 35, 500, True, [
        ("Frango xadrez", "Com arroz branco", 2990, False, False),
        ("Rolinho primavera", "4 unidades", 1490, True, True),
        ("Chop suey de legumes", "Com arroz branco", 2590, True, True),
    ]),
    ("Wok Expresso", "chinesa", 4.2, 25, 400, True, [
        ("Yakisoba de carne", "Individual", 3190, False, False),
        ("Arroz frito com legumes", "Com ovo", 2190, True, False),
        ("Guioza de legumes", "6 unidades", 1890, True, True),
    ]),

    # ---- pizza e italiana ----
    ("Pizzaria Lua Cheia", "pizza", 4.6, 45, 700, True, [
        ("Pizza quatro queijos grande", "Mussarela, provolone, gorgonzola e parmesão", 5990, True, False),
        ("Pizza de calabresa grande", "Com cebola roxa", 5490, False, False),
        ("Pizza de frango com catupiry grande", "Massa fina", 5790, False, False),
    ]),
    ("Fatia Quente", "pizza", 4.1, 20, 300, True, [
        ("Pizza calabresa brotinho", "Individual", 2190, False, False),
        ("Pizza de queijo brotinho", "Individual", 1990, True, False),
        ("Pizza de banana com canela brotinho", "Doce", 1890, True, False),
    ]),
    ("Massa Fresca da Aldeota", "italiana", 4.4, 40, 600, True, [
        ("Talharim ao sugo", "Molho de tomate fresco", 2890, True, True),
        ("Lasanha à bolonhesa", "Porção individual", 3490, False, False),
        ("Ravioli de ricota", "Ao molho branco", 3690, True, False),
    ]),

    # ---- hambúrguer e lanches ----
    ("Chapa 85", "hamburguer", 4.5, 30, 600, True, [
        ("Smash duplo", "Dois hambúrgueres, cheddar e picles", 3290, False, False),
        ("Burguer de cogumelo", "Pão brioche e rúcula", 2990, True, False),
        ("Onion rings", "Porção", 1690, True, True),
    ]),
    ("Brutus Burguer", "hamburguer", 3.9, 45, 800, True, [
        ("Brutus bacon", "Hambúrguer 200 g com bacon", 3890, False, False),
        ("Burguer vegano de grão-de-bico", "Pão sem leite", 3190, True, True),
        ("Milkshake de chocolate", "400 ml", 1890, True, False),
    ]),
    ("Pastelaria do Mercado", "lanches", 4.3, 25, 400, True, [
        ("Pastel de carne", "Grande", 1090, False, False),
        ("Pastel de queijo", "Grande", 990, True, False),
        ("Pastel de palmito", "Grande", 1190, True, True),
        ("Caldo de cana", "500 ml", 790, True, True),
    ]),
    ("Sanduba do Benfica", "lanches", 4.0, 20, 250, True, [
        ("Misto quente", "Pão de forma, presunto e queijo", 890, False, False),
        ("Sanduíche natural de frango", "Pão integral", 1290, False, False),
        ("Sanduíche de homus", "Com legumes grelhados", 1390, True, True),
    ]),

    # ---- caseira e marmita ----
    ("Marmitaria Bom Prato", "caseira", 4.2, 25, 0, True, [
        ("Marmita de carne moída", "Arroz, feijão e salada", 1890, False, False),
        ("Marmita de peixe grelhado", "Arroz, feijão e purê", 2390, False, False),
        ("Marmita vegana do dia", "Arroz integral, feijão e legumes", 1990, True, True),
    ]),
    ("Fogão a Lenha", "caseira", 4.5, 40, 500, True, [
        ("Frango caipira com quiabo", "Com angu", 3290, False, False),
        ("Costela no feijão", "Com arroz", 3690, False, False),
        ("Omelete de legumes", "Com salada", 1990, True, False),
    ]),
    ("Tempero de Mãe", "caseira", 4.6, 35, 300, True, [
        ("Bife acebolado", "Arroz, feijão e batata", 2490, False, False),
        ("Escondidinho de frango", "Com purê de macaxeira", 2590, False, False),
        ("Legumes refogados com arroz", "Com feijão", 1790, True, True),
    ]),

    # ---- frutos do mar e churrasco ----
    ("Maré Alta", "frutos do mar", 4.7, 55, 900, True, [
        ("Peixada cearense", "Serve 2 pessoas", 8990, False, False),
        ("Camarão ao alho e óleo", "Com arroz e fritas", 5490, False, False),
        ("Caranguejo", "3 unidades", 4290, False, False),
    ]),
    ("Barraca do Mucuripe", "frutos do mar", 4.3, 45, 700, True, [
        ("Isca de peixe", "Porção", 3290, False, False),
        ("Casquinha de caranguejo", "2 unidades", 2490, False, False),
        ("Macaxeira frita", "Porção", 1590, True, True),
    ]),
    ("Espeto do Seu Zé", "churrasco", 4.4, 35, 500, True, [
        ("Espetinho de carne", "Com baião e vinagrete", 1990, False, False),
        ("Espetinho de queijo coalho", "Com melaço", 1290, True, False),
        ("Espetinho de legumes", "Com farofa", 1490, True, True),
    ]),
    ("Churrascaria Gaúcho Cearense", "churrasco", 4.1, 60, 1000, True, [
        ("Picanha na chapa", "Serve 2 pessoas", 9890, False, False),
        ("Linguiça toscana", "Porção", 2890, False, False),
        ("Arroz carreteiro", "Porção", 2490, False, False),
    ]),

    # ---- árabe e saudável ----
    ("Esfiharia Oásis", "árabe", 4.3, 30, 500, True, [
        ("Esfiha de carne", "Unidade", 590, False, False),
        ("Esfiha de queijo", "Unidade", 590, True, False),
        ("Falafel com tahine", "6 unidades", 2290, True, True),
        ("Quibe assado", "Porção", 2690, False, False),
    ]),
    ("Cedro Libanês", "árabe", 4.6, 50, 800, True, [
        ("Kafta no prato", "Com arroz sírio e salada", 3690, False, False),
        ("Prato vegetariano árabe", "Homus, babaganuche, tabule e pão", 3290, True, True),
        ("Charuto de folha de uva", "8 unidades", 2890, True, True),
    ]),
    ("Folha & Grão", "saudável", 4.8, 30, 400, True, [
        ("Salada de quinoa", "Com legumes e molho de limão", 2890, True, True),
        ("Poke de salmão", "Arroz, salmão, manga e pepino", 3990, False, False),
        ("Wrap de frango", "Com salada", 2490, False, False),
        ("Suco verde", "500 ml", 1090, True, True),
    ]),
    ("Fit Express", "saudável", 4.0, 20, 300, True, [
        ("Frango grelhado com batata-doce", "Com brócolis", 2590, False, False),
        ("Tofu grelhado com legumes", "Com arroz integral", 2390, True, True),
        ("Iogurte com granola", "300 g", 1290, True, False),
    ]),

    # ---- açaí, doces e café ----
    ("Açaí do Porto", "açaí", 4.5, 20, 300, True, [
        ("Açaí 500 ml", "Com banana e granola", 1990, True, True),
        ("Açaí 300 ml", "Com leite em pó e paçoca", 1490, True, False),
        ("Cupuaçu 500 ml", "Com granola", 2090, True, True),
    ]),
    ("Gelateria Brisa", "sobremesas", 4.7, 30, 500, True, [
        ("Sorvete de tapioca", "2 bolas", 1490, True, False),
        ("Sorbet de cajá", "2 bolas, sem leite", 1390, True, True),
        ("Petit gâteau", "Com sorvete de creme", 2190, True, False),
    ]),
    ("Doceria Rapadura", "sobremesas", 4.4, 40, 500, True, [
        ("Cocada de forno", "Fatia", 890, True, False),
        ("Doce de leite com queijo", "Porção", 1190, True, False),
        ("Salada de frutas", "400 ml", 1290, True, True),
    ]),
    ("Café Sobral", "café", 4.6, 25, 400, True, [
        ("Café com tapioca", "Café coado e tapioca de manteiga", 1490, True, False),
        ("Pão de queijo", "6 unidades", 1190, True, False),
        ("Bolo de milho", "Fatia", 790, True, False),
    ]),

    # ---- fechados agora (o agente nunca deve sugerir) ----
    ("Padaria Aurora", "café", 4.2, 20, 300, False, [
        ("Pão na chapa", "Com manteiga", 690, True, False),
        ("Café com leite", "300 ml", 590, True, False),
    ]),
    ("Noite de Sushi", "japonesa", 4.5, 25, 500, False, [
        ("Combo noturno 30 peças", "Variado", 7990, False, False),
    ]),
]

# (codigo, tipo, valor, pedido_minimo_centavos, ativo)
CUPONS = [
    ("BEMVINDO10", "percentual", 10, 3000, True),  # 10% em pedidos a partir de R$ 30
    ("RANGO5", "fixo", 500, 2500, True),  # R$ 5 off a partir de R$ 25
    ("FRETEGRATIS", "frete_gratis", 0, 2000, True),  # frete grátis a partir de R$ 20
    ("JANTAR15", "percentual", 15, 5000, True),  # 15% em pedidos a partir de R$ 50
    ("VENCIDO20", "percentual", 20, 0, False),  # inativo: o agente deve recusar
]
