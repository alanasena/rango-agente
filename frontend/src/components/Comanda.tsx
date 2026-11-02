// A "comanda": o pedido sugerido, com o botão de confirmar
import type { Confirmacao, ResumoPedido } from "../tipos";

type Props = {
  pedido: ResumoPedido;
  confirmacao: Confirmacao;
  aoConfirmar: () => void;
};

export function Comanda({ pedido, confirmacao, aoConfirmar }: Props) {
  const temDesconto = pedido.desconto !== "R$ 0,00";

  return (
    <section className={`comanda estado-${confirmacao.estado}`} aria-label="Pedido sugerido">
      <h3 className="comanda-restaurante">{pedido.restaurante}</h3>

      <ul className="comanda-itens">
        {pedido.itens.map((item, i) => (
          <li key={i}>
            <span>
              {item.quantidade}× {item.prato}
            </span>
            <span>{item.valor}</span>
          </li>
        ))}
      </ul>

      <dl className="comanda-contas">
        <div>
          <dt>Subtotal</dt>
          <dd>{pedido.subtotal}</dd>
        </div>
        <div>
          <dt>Frete</dt>
          <dd>{pedido.frete === "R$ 0,00" ? "Grátis" : pedido.frete}</dd>
        </div>
        {temDesconto && (
          <div>
            <dt>Cupom {pedido.cupom_aplicado}</dt>
            <dd>− {pedido.desconto}</dd>
          </div>
        )}
        <div className="comanda-total">
          <dt>Total</dt>
          <dd>{pedido.total}</dd>
        </div>
      </dl>

      {pedido.avisos.length > 0 && (
        <ul className="comanda-avisos">
          {pedido.avisos.map((aviso, i) => (
            <li key={i}>{aviso}</li>
          ))}
        </ul>
      )}

      <div className="comanda-acao" aria-live="polite">
        {confirmacao.estado === "aguardando" && (
          <button className="botao-confirmar" onClick={aoConfirmar}>
            Confirmar pedido
          </button>
        )}
        {confirmacao.estado === "enviando" && (
          <button className="botao-confirmar" disabled>
            Confirmando...
          </button>
        )}
        {confirmacao.estado === "confirmado" && (
          <p className="comanda-confirmado">Pedido #{confirmacao.pedidoId} confirmado. Bom apetite!</p>
        )}
        {confirmacao.estado === "expirada" && (
          <p className="comanda-expirada">Esta sugestão foi substituída pela conversa mais nova.</p>
        )}
        {confirmacao.estado === "erro" && (
          <>
            <p className="comanda-erro">{confirmacao.mensagem}</p>
            <button className="botao-confirmar" onClick={aoConfirmar}>
              Tentar confirmar de novo
            </button>
          </>
        )}
      </div>
    </section>
  );
}
