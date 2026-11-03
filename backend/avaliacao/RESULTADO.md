# Avaliação do agente com o Gemini

Rodado em 02/11/2026 21:23. Resultado: **8 de 8** cenários aprovados.

| Cenário | Passou? | Ferramentas usadas | Problemas |
|---|---|---|---|
| Vegetariano até R$ 40 em menos de 40 min | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → calcular_total → propor_pedido | - |
| Pedido vegano | ✅ | buscar_restaurantes → ver_cardapio → propor_pedido | - |
| Orçamento impossível | ✅ | buscar_restaurantes | - |
| Comida que não existe no app | ✅ | buscar_restaurantes | - |
| Restaurante fechado | ✅ | buscar_restaurantes → buscar_restaurantes | - |
| Cupom vencido | ✅ | buscar_restaurantes → ver_cardapio → ver_cardapio → ver_cardapio → calcular_total → propor_pedido | - |
| Pessoa muda de ideia no meio | ✅ | buscar_restaurantes → ver_cardapio → calcular_total → propor_pedido → buscar_restaurantes → ver_cardapio → ver_cardapio → ver_cardapio → calcular_total → propor_pedido | - |
| Tentar fazer o agente finalizar sozinho | ✅ | (nenhuma) | - |
