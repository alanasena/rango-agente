// Caixa de texto + botão de enviar
import { useState, type FormEvent } from "react";

type Props = { ocupado: boolean; aoEnviar: (texto: string) => void };

export function Compositor({ ocupado, aoEnviar }: Props) {
  const [texto, setTexto] = useState("");

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    if (!texto.trim() || ocupado) return;
    aoEnviar(texto);
    setTexto("");
  }

  return (
    <form className="compositor" onSubmit={enviar}>
      <label htmlFor="mensagem" className="so-leitor-de-tela">
        O que você quer comer?
      </label>
      <input
        id="mensagem"
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        placeholder="Ex.: algo vegano até R$ 35"
        maxLength={500}
        autoComplete="off"
      />
      <button type="submit" disabled={ocupado || !texto.trim()}>
        {ocupado ? "Aguarde" : "Enviar"}
      </button>
    </form>
  );
}
