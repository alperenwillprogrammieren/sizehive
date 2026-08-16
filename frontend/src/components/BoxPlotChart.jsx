import { useState } from "react";

// Horizontal five-number-summary plot: whisker min–max, box p25–p75, median
// rule. The groups (brands, categories) are *nominal* — swapping their order
// changes nothing — so every box wears the same single series hue. Colouring
// them by value would re-encode what the box position already shows, and a
// one-series chart needs no legend: the title names what is plotted.

const ROW_HEIGHT = 30;
const BOX_HEIGHT = 14;
const LABEL_WIDTH = 150;
const VALUE_WIDTH = 68;
const PAD_TOP = 10;
const AXIS_HEIGHT = 26;
const WIDTH = 760;

function niceTicks(max, count = 4) {
  const raw = max / count;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? magnitude * 10;
  const ticks = [];
  for (let value = 0; value <= max + step / 2; value += step) ticks.push(value);
  return ticks;
}

function euro(value) {
  return `${value.toFixed(2)} €`;
}

export default function BoxPlotChart({ groups }) {
  const [hover, setHover] = useState(null);
  if (!groups.length) return <p className="coverage-note">Keine Gruppe erreicht die Mindestgröße.</p>;

  const max = Math.max(...groups.map((g) => g.max_eur));
  const ticks = niceTicks(max);
  const scaleMax = ticks[ticks.length - 1];

  const plotLeft = LABEL_WIDTH;
  const plotRight = WIDTH - VALUE_WIDTH;
  const x = (value) => plotLeft + (value / scaleMax) * (plotRight - plotLeft);

  const height = PAD_TOP + groups.length * ROW_HEIGHT + AXIS_HEIGHT;

  return (
    <div className="chart-wrap">
      <svg
        className="viz"
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label="Preisverteilung je Gruppe: Minimum, unteres Quartil, Median, oberes Quartil, Maximum"
      >
        {/* Gridlines: solid hairlines, one step off the surface. */}
        {ticks.map((tick) => (
          <line
            key={tick}
            x1={x(tick)}
            y1={PAD_TOP}
            x2={x(tick)}
            y2={PAD_TOP + groups.length * ROW_HEIGHT}
            stroke="var(--viz-grid)"
            strokeWidth="1"
          />
        ))}

        {groups.map((group, index) => {
          const y = PAD_TOP + index * ROW_HEIGHT + ROW_HEIGHT / 2;
          const isHovered = hover?.group === group.group;
          return (
            <g
              key={group.group}
              onMouseEnter={() => setHover({ group: group.group, y })}
              onMouseLeave={() => setHover(null)}
            >
              {/* Hit area spans the whole row, not just the box. */}
              <rect
                x={0}
                y={y - ROW_HEIGHT / 2}
                width={WIDTH}
                height={ROW_HEIGHT}
                fill={isHovered ? "var(--surface-muted)" : "transparent"}
              />
              <text x={0} y={y + 4} className="viz-label">
                {group.group}
              </text>

              {/* Whisker */}
              <line
                x1={x(group.min_eur)}
                y1={y}
                x2={x(group.max_eur)}
                y2={y}
                stroke="var(--viz-axis)"
                strokeWidth="1"
              />
              {[group.min_eur, group.max_eur].map((cap) => (
                <line
                  key={cap}
                  x1={x(cap)}
                  y1={y - 5}
                  x2={x(cap)}
                  y2={y + 5}
                  stroke="var(--viz-axis)"
                  strokeWidth="1"
                />
              ))}

              {/* Interquartile box */}
              <rect
                x={x(group.p25_eur)}
                y={y - BOX_HEIGHT / 2}
                width={Math.max(2, x(group.p75_eur) - x(group.p25_eur))}
                height={BOX_HEIGHT}
                rx="3"
                fill="var(--viz-series-1)"
                opacity={isHovered ? 1 : 0.85}
              />
              {/* Median, drawn in the surface colour so it reads as a gap. */}
              <line
                x1={x(group.median_eur)}
                y1={y - BOX_HEIGHT / 2}
                x2={x(group.median_eur)}
                y2={y + BOX_HEIGHT / 2}
                stroke="var(--surface)"
                strokeWidth="2"
              />

              {/* One direct label per row: the median is the point of the row. */}
              <text x={WIDTH} y={y + 4} className="viz-value" textAnchor="end">
                {group.median_eur.toFixed(0)} €
              </text>
            </g>
          );
        })}

        {/* Axis */}
        <line
          x1={plotLeft}
          y1={PAD_TOP + groups.length * ROW_HEIGHT}
          x2={plotRight}
          y2={PAD_TOP + groups.length * ROW_HEIGHT}
          stroke="var(--viz-axis)"
          strokeWidth="1"
        />
        {ticks.map((tick) => (
          <text
            key={tick}
            x={x(tick)}
            y={PAD_TOP + groups.length * ROW_HEIGHT + 16}
            className="viz-tick"
            textAnchor="middle"
          >
            {tick.toFixed(0)} €
          </text>
        ))}
      </svg>

      {hover && (
        <div className="viz-tooltip" style={{ top: `${(hover.y / height) * 100}%` }}>
          {(() => {
            const group = groups.find((g) => g.group === hover.group);
            return (
              <>
                <strong>{group.group}</strong>
                <span>{group.count} Angebote</span>
                <span>
                  Min {euro(group.min_eur)} · p25 {euro(group.p25_eur)}
                </span>
                <span>Median {euro(group.median_eur)}</span>
                <span>
                  p75 {euro(group.p75_eur)} · Max {euro(group.max_eur)}
                </span>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}
