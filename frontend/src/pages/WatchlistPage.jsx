import { Link } from "react-router-dom";
import { clearWatchlist, useWatchlist } from "../collections";
import { ResultCard } from "../components/ResultsList";
import { useVariantsByIds } from "../useVariants";

function formatSavedAt(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

/** Price move since the item was put on the Merkliste. The saved price is the
 *  only thing stored locally besides the id — everything else is live. */
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

export default function WatchlistPage() {
  const watchlist = useWatchlist();
  const ids = watchlist.map((entry) => entry.variant_id);
  const { items, loading } = useVariantsByIds(ids);

  const savedById = new Map(watchlist.map((entry) => [entry.variant_id, entry]));
  const missingCount = !loading && ids.length > items.length ? ids.length - items.length : 0;

  return (
    <div className="watchlist-page">
      <div className="page-header">
        <div>
          <h1>Merkliste</h1>
          <p className="tagline">
            Lokal in diesem Browser gespeichert — kein Konto nötig. Preise werden bei jedem Aufruf frisch geladen.
          </p>
        </div>
        {watchlist.length > 0 && (
          <button type="button" className="text-button" onClick={clearWatchlist}>
            Merkliste leeren
          </button>
        )}
      </div>

      {watchlist.length === 0 && (
        <div className="status-message">
          Noch nichts gemerkt. Tippe in der <Link to="/">Suche</Link> auf das ♡ an einem Artikel.
        </div>
      )}

      {watchlist.length > 0 && loading && <div className="status-message">Lädt…</div>}

      {items.length > 0 && (
        <div className="results-grid">
          {items.map((item) => {
            const entry = savedById.get(item.variant_id);
            return (
              <ResultCard key={item.variant_id} item={item}>
                <PriceSinceSaved
                  savedPrice={entry?.price_eur_at_save}
                  currentPrice={item.price_eur}
                  savedAt={entry?.saved_at}
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
