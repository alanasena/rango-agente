// Toda a lógica da conversa fica aqui; os componentes só desenham.
import { useCallback, useEffect, useRef, useState } from "react";
import { ConversaNaoEncontrada, ErroDaApi, confirmarPedido, criarConversa, enviarMensagem } from "./api";
import type { EventoAgente, Turno, TurnoAgente } from "./tipos";

let contador = 0;
const novoId = () => `t${++contador}`;

export function useConversa() {
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [ocupado, setOcupado] = useState(false);
  const [erroConexao, setErroConexao] = useState<string | null>(null);
  // O servidor grátis "dorme" quando ninguém usa e leva até 1 minuto para acordar
  const [acordando, setAcordando] = useState(false);
  const conversaId = useRef<string | null>(null);

  const garantirConversa = useCallback(async () => {
    if (!conversaId.current) conversaId.current = await criarConversa();
    return conversaId.current;
  }, []);

  useEffect(() => {
    const aviso = setTimeout(() => setAcordando(true), 2500);
    garantirConversa()
      .catch(() =>
        setErroConexao("O servidor do Rangô não respondeu. Recarregue a página para tentar de novo."),
      )
      .finally(() => {
        clearTimeout(aviso);
        setAcordando(false);
      });
    return () => clearTimeout(aviso);
  }, [garantirConversa]);

  const atualizarAgente = (id: string, mudar: (t: TurnoAgente) => TurnoAgente) =>
    setTurnos((lista) =>
      lista.map((t) => (t.id === id && t.autor === "agente" ? mudar(t) : t)),
    );

  const aplicarEvento = (id: string, evento: EventoAgente) =>
    atualizarAgente(id, (t) => {
      switch (evento.tipo) {
        case "passo":
          return { ...t, passos: [...t.passos, { ferramenta: evento.ferramenta, texto: evento.texto }] };
        case "resultado": {
          const passos = [...t.passos];
          const ultimo = passos[passos.length - 1];
          if (ultimo) passos[passos.length - 1] = { ...ultimo, resultado: evento.dados };
          return { ...t, passos };
        }
        case "proposta":
          return { ...t, proposta: evento.dados, confirmacao: { estado: "aguardando" } };
        case "resposta":
          return { ...t, texto: evento.texto };
        case "fim":
          return { ...t, terminou: true };
      }
    });

  const enviar = useCallback(
    async (texto: string) => {
      const limpo = texto.trim();
      if (!limpo || ocupado) return;

      const idAgente = novoId();
      setOcupado(true);
      setErroConexao(null);
      setTurnos((lista) => [
        // Uma mensagem nova cancela a proposta anterior (o back-end faz o mesmo)
        ...lista.map((t) =>
          t.autor === "agente" && t.confirmacao?.estado === "aguardando"
            ? { ...t, confirmacao: { estado: "expirada" as const } }
            : t,
        ),
        { id: novoId(), autor: "usuario", texto: limpo },
        { id: idAgente, autor: "agente", passos: [], terminou: false },
      ]);

      const tentar = async () =>
        enviarMensagem(await garantirConversa(), limpo, (e) => aplicarEvento(idAgente, e));

      try {
        try {
          await tentar();
        } catch (erro) {
          // O servidor reiniciou e esqueceu a conversa: começa outra e tenta de novo
          if (!(erro instanceof ConversaNaoEncontrada)) throw erro;
          conversaId.current = null;
          await tentar();
        }
      } catch (erro) {
        const mensagem =
          erro instanceof ErroDaApi
            ? erro.message
            : "Perdi a conexão com o servidor. Manda a mensagem de novo, por favor.";
        atualizarAgente(idAgente, (t) => ({ ...t, texto: t.texto ?? mensagem }));
      } finally {
        atualizarAgente(idAgente, (t) => ({ ...t, terminou: true }));
        setOcupado(false);
      }
    },
    [ocupado, garantirConversa],
  );

  const confirmar = useCallback(
    async (idAgente: string) => {
      atualizarAgente(idAgente, (t) => ({ ...t, confirmacao: { estado: "enviando" } }));
      try {
        const pedido = await confirmarPedido(await garantirConversa());
        atualizarAgente(idAgente, (t) => ({
          ...t,
          confirmacao: { estado: "confirmado", pedidoId: pedido.pedido_id, total: pedido.total },
        }));
      } catch (erro) {
        const mensagem = erro instanceof Error ? erro.message : "Não deu para confirmar.";
        atualizarAgente(idAgente, (t) => ({ ...t, confirmacao: { estado: "erro", mensagem } }));
      }
    },
    [garantirConversa],
  );

  return { turnos, ocupado, erroConexao, acordando, enviar, confirmar };
}
