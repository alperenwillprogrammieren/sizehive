const WIDTH = 640;
const HEIGHT = 220;
const PAD = 36;

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
}

export default function PriceChart({ points }) {
  if (!points || points.length === 0) return null;

  const prices = points.map((p) => p.price_eur);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  const x = (i) => PAD + (i / Math.max(1, points.length - 1)) * (WIDTH - 2 * PAD);
  const y = (v) => HEIGHT - PAD - ((v - min) / range) * (HEIGHT - 2 * PAD);

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(p.price_eur).toFixed(1)}`).join(" ");

  return (
    <svg className="price-chart" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Preisverlauf">
      <line x1={PAD} y1={HEIGHT - PAD} x2={WIDTH - PAD} y2={HEIGHT - PAD} stroke="#d0d0d5" />
      <line x1={PAD} y1={PAD} x2={PAD} y2={HEIGHT - PAD} stroke="#d0d0d5" />

      <text x={PAD} y={PAD - 10} fontSize="11" fill="#6b6b70">
        {max.toFixed(2)} €
      </text>
      <text x={PAD} y={HEIGHT - PAD + 16} fontSize="11" fill="#6b6b70">
        {min.toFixed(2)} €
      </text>

      <path d={linePath} fill="none" stroke="#1c1c1e" strokeWidth="2" />
      {points.map((p, i) => (
        <circle
          key={p.captured_at}
          cx={x(i)}
          cy={y(p.price_eur)}
          r={p.in_stock ? 3 : 3}
          fill={p.in_stock ? "#1c1c1e" : "#d0263d"}
        >
          <title>
            {formatDate(p.captured_at)}: {p.price_eur.toFixed(2)} € {p.in_stock ? "" : "(nicht verfügbar)"}
          </title>
        </circle>
      ))}

      <text x={PAD} y={HEIGHT - 6} fontSize="11" fill="#9a9aa0">
        {formatDate(points[0].captured_at)}
      </text>
      <text x={WIDTH - PAD} y={HEIGHT - 6} fontSize="11" fill="#9a9aa0" textAnchor="end">
        {formatDate(points[points.length - 1].captured_at)}
      </text>
    </svg>
  );
}
