// Transforma **texto** em negrito, sem usar HTML vindo de fora (mais seguro)
export function TextoComNegrito({ texto }: { texto: string }) {
  const partes = texto.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {partes.map((parte, i) =>
        parte.startsWith("**") && parte.endsWith("**") ? (
          <strong key={i}>{parte.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{parte}</span>
        ),
      )}
    </>
  );
}
