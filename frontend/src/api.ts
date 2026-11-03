// Conversa com a API do Rangô (back-end em FastAPI)
import type { EventoAgente, PedidoConfirmado } from "./tipos";

const URL_API = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ConversaNaoEncontrada extends Error {}

/** Erro com uma mensagem que pode ser mostrada para a pessoa (ex.: limite de mensagens). */
export class ErroDaApi extends Error {}

async function mensagemDeErro(resposta: Response, padrao: string): Promise<string> {
  try {
    const dados = await resposta.json();
    return typeof dados.detail === "string" ? dados.detail : padrao;
  } catch {
    return padrao;
  }
}

export async function criarConversa(): Promise<string> {
  const resposta = await fetch(`${URL_API}/conversas`, { method: "POST" });
  if (!resposta.ok) throw new Error("Não deu para conectar com o Rangô.");
  const dados = (await resposta.json()) as { conversa_id: string };
  return dados.conversa_id;
}

/**
 * Lê pedacinhos no formato SSE ("data: {...}\n\n") e devolve os eventos completos.
 * O que sobrar incompleto volta em `resto`, para juntar com o próximo pedaço.
 */
export function lerEventosSSE(texto: string): { eventos: EventoAgente[]; resto: string } {
  const blocos = texto.split("\n\n");
  const resto = blocos.pop() ?? "";
  const eventos: EventoAgente[] = [];
  for (const bloco of blocos) {
    for (const linha of bloco.split("\n")) {
      if (linha.startsWith("data: ")) {
        eventos.push(JSON.parse(linha.slice(6)) as EventoAgente);
      }
    }
  }
  return { eventos, resto };
}

/** Manda a mensagem e vai chamando `aoReceber` a cada evento, AO VIVO. */
export async function enviarMensagem(
  conversaId: string,
  texto: string,
  aoReceber: (evento: EventoAgente) => void,
): Promise<void> {
  const resposta = await fetch(`${URL_API}/conversas/${conversaId}/mensagens`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
  if (resposta.status === 404) throw new ConversaNaoEncontrada();
  if (!resposta.ok || !resposta.body) {
    throw new ErroDaApi(await mensagemDeErro(resposta, "O Rangô não conseguiu responder."));
  }

  const leitor = resposta.body.getReader();
  const decodificador = new TextDecoder();
  let acumulado = "";

  while (true) {
    const { done, value } = await leitor.read();
    if (done) break;
    acumulado += decodificador.decode(value, { stream: true });
    const { eventos, resto } = lerEventosSSE(acumulado);
    acumulado = resto;
    eventos.forEach(aoReceber);
  }
}

export async function confirmarPedido(conversaId: string): Promise<PedidoConfirmado> {
  const resposta = await fetch(`${URL_API}/conversas/${conversaId}/confirmar`, { method: "POST" });
  const dados = await resposta.json();
  if (!resposta.ok) throw new Error(dados.detail ?? "Não deu para confirmar o pedido.");
  return dados as PedidoConfirmado;
}
