import { describe, expect, it } from "vitest";
import { lerEventosSSE } from "./api";

describe("lerEventosSSE", () => {
  it("lê eventos completos", () => {
    const { eventos, resto } = lerEventosSSE(
      'data: {"tipo": "passo", "texto": "Buscando...", "ferramenta": "buscar_restaurantes"}\n\n' +
        'data: {"tipo": "fim"}\n\n',
    );
    expect(eventos.map((e) => e.tipo)).toEqual(["passo", "fim"]);
    expect(resto).toBe("");
  });

  it("guarda o pedaço incompleto para depois", () => {
    const primeiro = lerEventosSSE('data: {"tipo": "fim"}\n\ndata: {"tipo": "res');
    expect(primeiro.eventos).toHaveLength(1);
    expect(primeiro.resto).toBe('data: {"tipo": "res');

    const segundo = lerEventosSSE(primeiro.resto + 'posta", "texto": "Oi"}\n\n');
    expect(segundo.eventos).toEqual([{ tipo: "resposta", texto: "Oi" }]);
  });
});
