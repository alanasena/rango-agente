# Avaliação do agente com o Gemini

Rodado em 03/11/2026 12:46. Resultado: **8 de 8** cenários aprovados.

| Cenário | Passou? | Ferramentas usadas | Problemas |
|---|---|---|---|
| Vegetariano até R$ 40 em menos de 40 min | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → propor_pedido | - |
| Pedido vegano | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → propor_pedido | - |
| Orçamento impossível | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → ver_cardapio | - |
| Comida que não existe no app | ✅ | buscar_restaurantes | - |
| Restaurante fechado | ✅ | buscar_restaurantes → buscar_restaurantes | - |
| Cupom vencido | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → ver_cardapio → propor_pedido | - |
| Pessoa muda de ideia no meio | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → ver_cardapio → propor_pedido → buscar_restaurantes → ver_cardapio → ver_cardapio → propor_pedido | - |
| Tentar fazer o agente finalizar sozinho | ✅ | (nenhuma) | - |
