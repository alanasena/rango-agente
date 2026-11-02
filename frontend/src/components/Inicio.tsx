// Tela vazia: convida a pessoa a começar
const SUGESTOES = [
  "Jantar vegetariano até R$ 40 que chegue em menos de 40 minutos",
  "Algo vegano e barato",
  "Uma pizza média e um refrigerante, com o cupom RANGO5",
  "Sushi em 20 minutos",
];

export function Inicio({ aoEscolher }: { aoEscolher: (texto: string) => void }) {
  return (
    <div className="inicio">
      <h2 className="inicio-titulo">O que vai ser hoje?</h2>
      <p className="inicio-texto">
        Diga o que você quer, quanto quer gastar e com que pressa. O Rangô procura, compara e
        monta o pedido. Você só confirma.
      </p>
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
