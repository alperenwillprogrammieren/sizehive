import { useState } from "react";

// Deviation from a baseline is a *polarity* question, so it takes the
// diverging pair: one hue above, the other below, with a neutral gray at
// zero. Not the status palette — "costs more" is not "bad", and status
// colours are reserved.

const ROW_HEIGHT = 28;
const BAR_HEIGHT = 14;
const LABEL_WIDTH = 130;
const VALUE_WIDTH = 56;
const WIDTH = 620;
const PAD_TOP = 8;
const PAD_BOTTOM = 8;

export default function DivergingBars({ rows, baselineLabel }) {
  const [hover, setHover] = useState(null);
  if (!rows.length) return null;

  const extent = Math.max(10, ...rows.map((row) => Math.abs(row.delta_pct)));
  // Reserve a value-label lane on *both* sides: a bar at full extent ends at
  // the plot edge, and its label is drawn beyond that end. Without the left
  // lane the label of a large negative value lands on the row-label column.
  const plotLeft = LABEL_WIDTH + VALUE_WIDTH;
  const plotRight = WIDTH - VALUE_WIDTH;
  const center = (plotLeft + plotRight) / 2;
  const halfWidth = (plotRight - plotLeft) / 2;
  const x = (pct) => center + (pct / extent) * halfWidth;

  const height = PAD_TOP + rows.length * ROW_HEIGHT + PAD_BOTTOM;

  return (
    <div className="chart-wrap">
      <svg
        className="viz"
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label={`Abweichung des Medianpreises je Wert gegenüber ${baselineLabel}`}
      >
        {/* Neutral midpoint: the "no deviation" line. */}
        <line
          x1={center}
          y1={PAD_TOP}
          x2={center}
          y2={PAD_TOP + rows.length * ROW_HEIGHT}
          stroke="var(--viz-mid)"
          strokeWidth="2"
        />

        {rows.map((row, index) => {
          const y = PAD_TOP + index * ROW_HEIGHT + ROW_HEIGHT / 2;
          const positive = row.delta_pct >= 0;
          const end = x(row.delta_pct);
          const barWidth = Math.max(1, Math.abs(end - center));
          const isHovered = hover?.value === row.value;

          return (
            <g
              key={row.value}
              onMouseEnter={() => setHover({ value: row.value, y })}
              onMouseLeave={() => setHover(null)}
            >
              <rect
                x={0}
                y={y - ROW_HEIGHT / 2}
                width={WIDTH}
                height={ROW_HEIGHT}
                fill={isHovered ? "var(--surface-muted)" : "transparent"}
              />
              <text x={0} y={y + 4} className="viz-label">
                {row.value.replace(/_/g, " ")}
              </text>

              <rect
                x={positive ? center : end}
                y={y - BAR_HEIGHT / 2}
                width={barWidth}
                height={BAR_HEIGHT}
                rx="3"
                fill={positive ? "var(--viz-pos)" : "var(--viz-neg)"}
                opacity={isHovered ? 1 : 0.85}
              />

              <text
                x={positive ? Math.min(end + 6, WIDTH - 4) : Math.max(end - 6, 4)}
                y={y + 4}
                className="viz-value"
                textAnchor={positive ? "start" : "end"}
              >
                {row.delta_pct > 0 ? "+" : ""}
                {row.delta_pct.toFixed(0)} %
              </text>
            </g>
          );
        })}
      </svg>

      {hover && (
        <div className="viz-tooltip" style={{ top: `${(hover.y / height) * 100}%` }}>
          {(() => {
            const row = rows.find((r) => r.value === hover.value);
            return (
              <>
                <strong>{row.value.replace(/_/g, " ")}</strong>
                <span>{row.count} Angebote</span>
                <span>Median {row.median_eur.toFixed(2)} €</span>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}
