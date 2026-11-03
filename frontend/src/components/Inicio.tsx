// Tela vazia: convida a pessoa a começar
import { Mascote } from "./Mascote";

const SUGESTOES = [
  "Jantar vegetariano até R$ 40 que chegue em menos de 40 minutos",
  "Algo vegano e barato",
  "Uma pizza média e um refrigerante, com o cupom RANGO5",
  "Sushi em 20 minutos",
];

export function Inicio({ aoEscolher }: { aoEscolher: (texto: string) => void }) {
  return (
    <div className="inicio">
      <section className="vitrine">
        <div className="vitrine-cartaz">
          <h2 className="vitrine-titulo">
            O que vai
            <br />
            ser hoje?
          </h2>
          <Mascote className="vitrine-mascote" comFundo={false} />
        </div>

        {/* faixas com frase, como as da referência */}
        <p className="faixa faixa-verde">Fala o que você quer comer, quanto quer gastar e com que pressa</p>
        <p className="faixa faixa-creme">
          <strong>Pede</strong> primeiro, <strong>confirma</strong> depois
        </p>
      </section>

      <h3 className="sugestoes-titulo">Pra começar, tenta uma dessas:</h3>
      <ul className="sugestoes">
        {SUGESTOES.map((s) => (
          <li key={s}>
            <button onClick={() => aoEscolher(s)}>{s}</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
