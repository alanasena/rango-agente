// Mascote do Rangô: uma panelinha sorridente soltando vapor (desenho original)

type Props = { className?: string; comFundo?: boolean };

export function Mascote({ className, comFundo = true }: Props) {
  return (
    <svg className={className} viewBox="0 0 120 120" role="img" aria-label="Mascote do Rangô: uma panelinha sorrindo">
      {comFundo && <circle cx="60" cy="60" r="58" fill="#EC7520" />}
      <g fill="none" stroke="#0F4619" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
        {/* vapor */}
        <path d="M46 30c-5-5 5-8 0-13" />
        <path d="M60 27c-5-5 5-8 0-13" />
        <path d="M74 30c-5-5 5-8 0-13" />
        {/* tampa */}
        <path d="M24 52c8-11 64-11 72 0Z" fill="#F9F1E4" />
        <circle cx="60" cy="38" r="4.5" fill="#F9F1E4" />
        {/* alças */}
        <path d="M27 64h-8a4 4 0 0 0 0 8h8M93 64h8a4 4 0 0 1 0 8h-8" fill="#F9F1E4" />
        {/* corpo */}
        <path d="M26 55h68v20c0 15-11 25-26 25H52c-15 0-26-10-26-25Z" fill="#F9F1E4" />
        {/* rostinho */}
        <path d="M42 71q5-6 10 0M68 71q5-6 10 0" />
        <path d="M50 81q10 10 20 0" fill="#0F4619" />
      </g>
      <circle cx="40" cy="80" r="4.5" fill="#FDB882" />
      <circle cx="80" cy="80" r="4.5" fill="#FDB882" />
    </svg>
  );
}
