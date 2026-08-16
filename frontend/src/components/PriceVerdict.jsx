function euro(value) {
  return `${value.toFixed(2)} €`;
}

function Row({ label, value, note }) {
  if (value === null || value === undefined) return null;
  return (
    <div className="verdict-row">
      <span className="verdict-label">{label}</span>
      <span className="verdict-value">{value}</span>
      {note && <span className="verdict-note">{note}</span>}
    </div>
  );
}

/** Puts the current price in context of the variant's own recorded history,
 *  which is a different question from the percentile score (that one compares
 *  against other articles in the category). */
export default function PriceVerdict({ stats, currentPrice }) {
  if (!stats) return null;

  const claimGap = stats.claimed_discount_pct - stats.real_discount_pct;

  let headline;
  let tone;
  if (stats.is_all_time_low) {
    headline = "Günstigster Preis, seit wir diesen Artikel beobachten.";
    tone = "good";
  } else if (stats.days_since_cheaper === null) {
    headline = "Dieser Preis war noch nie niedriger.";
    tone = "good";
  } else if (stats.days_since_cheaper <= 7) {
    headline = `Vor ${stats.days_since_cheaper} Tagen war der Artikel bereits günstiger.`;
    tone = "warn";
  } else {
    headline = `So günstig wie zuletzt vor ${stats.days_since_cheaper} Tagen.`;
    tone = "neutral";
  }

  return (
    <div className="price-verdict">
      <div className={`verdict-headline ${tone}`}>{headline}</div>

      <div className="verdict-grid">
        <Row label="Aktuell" value={euro(currentPrice)} />
        <Row label="Tiefstpreis" value={euro(stats.all_time_low_eur)} />
        <Row label="Höchstpreis" value={euro(stats.all_time_high_eur)} />
        <Row
          label="Tief (30 Tage)"
          value={stats.low_30d_eur !== null ? euro(stats.low_30d_eur) : null}
        />
        <Row
          label="Median (90 Tage)"
          value={stats.median_90d_eur !== null ? euro(stats.median_90d_eur) : null}
        />
      </div>

      <div className="verdict-discounts">
        <div className="verdict-discount">
          <span className="verdict-label">Rabatt laut Shop</span>
          <span className="verdict-value">−{stats.claimed_discount_pct.toFixed(0)} %</span>
          <span className="verdict-note">gegen den Streichpreis</span>
        </div>
        <div className="verdict-discount">
          <span className="verdict-label">Tatsächlicher Rabatt</span>
          <span className="verdict-value">−{stats.real_discount_pct.toFixed(0)} %</span>
          <span className="verdict-note">gegen den höchsten je verlangten Preis</span>
        </div>
      </div>

      {claimGap >= 5 && (
        <div className="verdict-gap">
          Der beworbene Rabatt liegt {claimGap.toFixed(0)} Prozentpunkte über dem, was gegenüber dem höchsten
          tatsächlich verlangten Preis gespart wird.
        </div>
      )}

      <p className="verdict-basis">
        Basis: {stats.snapshot_count} Preis-Momentaufnahmen seit{" "}
        {new Date(stats.first_seen).toLocaleDateString("de-DE")}.
      </p>
    </div>
  );
}
