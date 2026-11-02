// A "trilha": mostra cada ferramenta que o agente usou, na ordem, ao vivo
import type { Passo } from "../tipos";

type Dados = Record<string, any>;

const plural = (n: number, palavra: string) => `${n} ${palavra}${n === 1 ? "" : "s"}`;

function resumir(passo: Passo): string | null {
  const r = passo.resultado as Dados | undefined;
  if (!r) return null;
  if (typeof r.erro === "string") return r.erro;

  switch (passo.ferramenta) {
    case "buscar_restaurantes": {
      const n = r.restaurantes?.length ?? 0;
      return n === 0 ? "Nenhum restaurante com esses filtros" : `${plural(n, "restaurante")} encontrado${n === 1 ? "" : "s"}`;
    }
    case "ver_cardapio":
      return `Cardápio de ${r.restaurante}: ${plural(r.pratos?.length ?? 0, "prato")}`;
    case "calcular_total":
      return r.dentro_do_orcamento === false ? `${r.total}, passa do orçamento` : `Total de ${r.total}`;
    case "propor_pedido":
      return "Sugestão pronta";
    default:
      return null;
  }
}

// O que aparece ao abrir "Ver detalhes": uma lista legível, não o JSON cru
function Detalhes({ passo }: { passo: Passo }) {
  const r = passo.resultado as Dados;

  if (passo.ferramenta === "buscar_restaurantes" && r.restaurantes?.length) {
    return (
      <ul className="detalhes-lista">
        {r.restaurantes.map((rest: Dados) => (
          <li key={rest.id}>
            <span className="detalhes-nome">{rest.nome}</span>
            <span className="detalhes-info detalhes-colunas">
              <span>★ {rest.nota.toFixed(1).replace(".", ",")}</span>
              <span>{rest.tempo_entrega_min} min</span>
              <span>frete {rest.frete_centavos === 0 ? "grátis" : rest.frete}</span>
            </span>
          </li>
        ))}
      </ul>
    );
  }

  if (passo.ferramenta === "ver_cardapio" && r.pratos?.length) {
    return (
      <ul className="detalhes-lista">
        {r.pratos.map((prato: Dados) => (
          <li key={prato.id}>
            <span className="detalhes-nome">
              {prato.nome}
              {prato.vegano ? (
                <span className="etiqueta">vegano</span>
              ) : prato.vegetariano ? (
                <span className="etiqueta">vegetariano</span>
              ) : null}
            </span>
            <span className="detalhes-info">{prato.preco}</span>
          </li>
        ))}
      </ul>
    );
  }

  const conta = passo.ferramenta === "propor_pedido" ? r.resumo : r;
  if (conta?.itens) {
    return (
      <ul className="detalhes-lista">
        {conta.itens.map((item: Dados, i: number) => (
          <li key={i}>
            <span className="detalhes-nome">
              {item.quantidade}× {item.prato}
            </span>
            <span className="detalhes-info">{item.valor}</span>
          </li>
        ))}
        <li>
          <span className="detalhes-nome">Frete</span>
          <span className="detalhes-info">{conta.frete}</span>
        </li>
        {conta.desconto !== "R$ 0,00" && (
          <li>
            <span className="detalhes-nome">Desconto</span>
            <span className="detalhes-info">− {conta.desconto}</span>
          </li>
        )}
      </ul>
    );
  }

  return null;
}

function temDetalhes(passo: Passo): boolean {
  const r = passo.resultado as Dados | undefined;
  if (!r || r.erro) return false;
  return Boolean(r.restaurantes?.length || r.pratos?.length || r.itens || r.resumo);
}

export function TrilhaDoAgente({ passos, pensando }: { passos: Passo[]; pensando: boolean }) {
  if (passos.length === 0 && !pensando) return null;

  return (
    <ol className="trilha" aria-label="O que o agente fez">
      {passos.map((passo, i) => {
        const resumo = resumir(passo);
        const emAndamento = !passo.resultado;
        const deuErro = typeof passo.resultado?.erro === "string";
        return (
          <li key={i} className={`trilha-passo ${emAndamento ? "em-andamento" : ""} ${deuErro ? "com-erro" : ""}`}>
            <span className="trilha-marca" aria-hidden="true" />
            <div>
              <p className="trilha-texto">{passo.texto}</p>
              {resumo && <p className="trilha-resumo">{resumo}</p>}
              {temDetalhes(passo) && (
                <details className="trilha-detalhes">
                  <summary>Ver detalhes</summary>
                  <Detalhes passo={passo} />
                </details>
              )}
            </div>
          </li>
        );
      })}
      {pensando && passos.every((p) => p.resultado) && (
        <li className="trilha-passo em-andamento">
          <span className="trilha-marca" aria-hidden="true" />
          <p className="trilha-texto">Pensando...</p>
        </li>
      )}
    </ol>
  );
}
