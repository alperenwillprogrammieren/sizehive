import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../authContext";
import { ResultCard } from "../components/ResultsList";
import { useVariantsByIds } from "../useVariants";
import { useWatchlist } from "../watchlistContext";

function formatSavedAt(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

/** Price move since the item was put on the Merkliste. The saved price is
 *  a deliberately historical value — everything else is live. */
function PriceSinceSaved({ savedPrice, currentPrice, savedAt }) {
  const saved = formatSavedAt(savedAt);
  if (typeof savedPrice !== "number") {
    return saved ? <div className="watch-delta neutral">Gemerkt am {saved}</div> : null;
  }

  const delta = currentPrice - savedPrice;
  const suffix = saved ? ` · gemerkt am ${saved}` : "";
  if (Math.abs(delta) < 0.005) {
    return <div className="watch-delta neutral">Unverändert seit dem Merken{suffix}</div>;
  }

  const pct = savedPrice > 0 ? Math.abs(delta / savedPrice) * 100 : 0;
  const cheaper = delta < 0;
  return (
    <div className={`watch-delta ${cheaper ? "down" : "up"}`}>
      {cheaper ? "▼" : "▲"} {Math.abs(delta).toFixed(2)} € ({pct.toFixed(0)} %) {cheaper ? "günstiger" : "teurer"} als beim
      Merken{suffix}
    </div>
  );
}

/** Offered once after login, when the browser still holds entries that the
 *  account doesn't have. */
function ImportBanner() {
  const { importLocal, localCount, entries } = useWatchlist();
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const serverIds = new Set(entries.map((entry) => entry.variant_id));
  const pending = localCount > 0 && !result;
  if (!pending) return result ? <div className="import-banner done">{result} übernommen.</div> : null;

  return (
    <div className="import-banner">
      <span>
        In diesem Browser liegen {localCount} lokal gemerkte Artikel
        {serverIds.size > 0 ? " (teils schon im Konto)" : ""}.
      </span>
      <button
        type="button"
        className="chip"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          try {
            const outcome = await importLocal();
            setResult(`${outcome.imported} Artikel`);
          } finally {
            setBusy(false);
          }
        }}
      >
        Ins Konto übernehmen
      </button>
    </div>
  );
}

export default function WatchlistPage() {
  const { user } = useAuth();
  const { entries, clear, backend, loading: listLoading } = useWatchlist();
  const ids = entries.map((entry) => entry.variant_id);
  const { items, loading } = useVariantsByIds(ids);

  const savedById = new Map(entries.map((entry) => [entry.variant_id, entry]));
  const missingCount = !loading && ids.length > items.length ? ids.length - items.length : 0;

  return (
    <div className="watchlist-page">
      <div className="page-header">
        <div>
          <h1>Merkliste</h1>
          <p className="tagline">
            {backend === "server"
              ? `Im Konto gespeichert (${user.email}) — auf allen Geräten verfügbar.`
              : "Lokal in diesem Browser gespeichert. Mit einem Konto ist sie geräteübergreifend verfügbar."}{" "}
            Preise werden bei jedem Aufruf frisch geladen.
          </p>
        </div>
        {entries.length > 0 && (
          <button type="button" className="text-button" onClick={clear}>
            Merkliste leeren
          </button>
        )}
      </div>

      {backend === "server" && <ImportBanner />}

      {entries.length === 0 && !listLoading && (
        <div className="status-message">
          Noch nichts gemerkt. Tippe in der <Link to="/">Suche</Link> auf das ♡ an einem Artikel.
        </div>
      )}

      {entries.length > 0 && loading && <div className="status-message">Lädt…</div>}

      {items.length > 0 && (
        <div className="results-grid">
          {items.map((item) => {
            const entry = savedById.get(item.variant_id);
            return (
              <ResultCard key={item.variant_id} item={item}>
                <PriceSinceSaved
                  savedPrice={entry?.price_eur_at_save}
                  currentPrice={item.price_eur}
                  savedAt={entry?.created_at ?? entry?.saved_at}
                />
              </ResultCard>
            );
          })}
        </div>
      )}

      {missingCount > 0 && (
        <p className="status-message">
          {missingCount} gemerkte{missingCount === 1 ? "r Artikel ist" : " Artikel sind"} nicht mehr im Katalog.
        </p>
      )}
    </div>
  );
}
