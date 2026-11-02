// Formato dos dados que chegam da API

export type ItemResumo = { prato: string; quantidade: number; valor: string };

export type ResumoPedido = {
  restaurante: string;
  itens: ItemResumo[];
  subtotal: string;
  frete: string;
  desconto: string;
  total: string;
  cupom_aplicado: string | null;
  avisos: string[];
};

export type EventoAgente =
  | { tipo: "passo"; texto: string; ferramenta: string }
  | { tipo: "resultado"; ferramenta: string; dados: Record<string, unknown> }
  | { tipo: "proposta"; dados: ResumoPedido }
  | { tipo: "resposta"; texto: string }
  | { tipo: "fim" };

export type PedidoConfirmado = { pedido_id: number; status: string; total: string };

// Formato que a TELA usa para desenhar a conversa

export type Passo = {
  ferramenta: string;
  texto: string;
  resultado?: Record<string, unknown>;
};

export type Confirmacao =
  | { estado: "aguardando" }
  | { estado: "enviando" }
  | { estado: "confirmado"; pedidoId: number; total: string }
  | { estado: "expirada" }
  | { estado: "erro"; mensagem: string };

export type TurnoUsuario = { id: string; autor: "usuario"; texto: string };

export type TurnoAgente = {
  id: string;
  autor: "agente";
  passos: Passo[];
  proposta?: ResumoPedido;
  confirmacao?: Confirmacao;
  texto?: string;
  terminou: boolean;
};

export type Turno = TurnoUsuario | TurnoAgente;
