import { useEffect, useRef } from "react";
import { Comanda } from "./components/Comanda";
import { Compositor } from "./components/Compositor";
import { Inicio } from "./components/Inicio";
import { Mascote } from "./components/Mascote";
import { TextoComNegrito } from "./components/TextoComNegrito";
import { TrilhaDoAgente } from "./components/TrilhaDoAgente";
import { useConversa } from "./useConversa";

export default function App() {
  const { turnos, ocupado, erroConexao, acordando, enviar, confirmar, novaConversa } = useConversa();
  const fimDaLista = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // só rola para o fim quando já tem conversa (senão esconderia o topo da tela inicial)
    if (turnos.length > 0) fimDaLista.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turnos]);

  return (
    <div className="pagina">
      <header className="cabecalho">
        {/* o conteúdo do cabeçalho fica alinhado com a coluna da conversa */}
        <div className="cabecalho-conteudo">
          <div>
            <h1 className="marca">
              <Mascote className="marca-mascote" />
              <span>Rangô</span>
            </h1>
            <p className="cabecalho-nota">Pedidos com IA. Restaurantes e preços fictícios, projeto de portfólio</p>
          </div>
          {turnos.length > 0 && (
            <button
              className="botao-nova-conversa"
              onClick={novaConversa}
              disabled={ocupado}
              title={ocupado ? "Espere o Rangô terminar de responder" : undefined}
            >
              <span aria-hidden="true">+</span> Nova conversa
            </button>
          )}
        </div>
      </header>

      <main className="conversa" aria-live="polite">
        {acordando && (
          <p className="aviso-acordando">
            Ligando o servidor. Na primeira visita isso pode levar até 1 minuto.
          </p>
        )}
        {erroConexao && <p className="aviso-conexao">{erroConexao}</p>}
        {turnos.length === 0 && <Inicio aoEscolher={enviar} />}

        {turnos.map((turno) =>
          turno.autor === "usuario" ? (
            <p key={turno.id} className="balao-usuario">
              {turno.texto}
            </p>
          ) : (
            <article key={turno.id} className="turno-agente">
              <TrilhaDoAgente passos={turno.passos} pensando={!turno.terminou} />
              {turno.texto && (
                <p className="resposta-agente">
                  <TextoComNegrito texto={turno.texto} />
                </p>
              )}
              {turno.proposta && turno.confirmacao && (
                <Comanda
                  pedido={turno.proposta}
                  confirmacao={turno.confirmacao}
                  aoConfirmar={() => confirmar(turno.id)}
                />
              )}
            </article>
          ),
        )}
        <div ref={fimDaLista} />
      </main>

      <Compositor ocupado={ocupado} aoEnviar={enviar} />
    </div>
  );
}
