import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchDeals, fetchFacets } from "../api";
import { ResultCard } from "../components/ResultsList";

const WINDOW_OPTIONS = [
  { value: "7", label: "7 Tage" },
  { value: "14", label: "14 Tage" },
  { value: "30", label: "30 Tage" },
];

const MIN_DROP_OPTIONS = [
  { value: "5", label: "ab 5 %" },
  { value: "10", label: "ab 10 %" },
  { value: "25", label: "ab 25 %" },
  { value: "40", label: "ab 40 %" },
];

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

/** The measured drop, plus — when the shop's struck-through claim differs
 *  from what we recorded — what the shop says instead. */
function DealBadge({ item, windowDays }) {
  const claimOverstated = item.discount_pct - item.drop_pct >= 5;

  return (
    <div className="deal-badge">
      <div className="deal-headline">
        <strong>−{item.drop_pct.toFixed(0)} %</strong> gegenüber {item.reference_price_eur.toFixed(2)} € vor{" "}
        {windowDays} Tagen
        <span className="deal-date"> (Stand {formatDate(item.reference_captured_at)})</span>
      </div>
      {item.is_all_time_low && <div className="deal-flag low">Günstigster je erfasster Preis</div>}
      {claimOverstated && (
        <div className="deal-flag claim">
          Shop wirbt mit −{item.discount_pct.toFixed(0)} % auf den Streichpreis
        </div>
      )}
    </div>
  );
}

export default function DealsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const windowDays = searchParams.get("window_days") || "7";
  const minDrop = searchParams.get("min_drop_pct") || "10";
  const category = searchParams.get("category") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);

  const [data, setData] = useState({ total: 0, results: [], page: 1, page_size: 20, window_days: 7 });
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFacets(new URLSearchParams())
      .then((facets) => setCategories((facets.facets.category || []).map((option) => option.value)))
      .catch(console.error);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams({ window_days: windowDays, min_drop_pct: minDrop, page: String(page) });
    if (category) params.set("category", category);

    let cancelled = false;
    setLoading(true);
    fetchDeals(params)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => console.error(err))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [windowDays, minDrop, category, page]);

  // Every control writes to the URL, so a deals view stays shareable and
  // reload-proof exactly like the search page.
  const update = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next);
  };

  const totalPages = Math.max(1, Math.ceil(data.total / (data.page_size || 20)));

  return (
    <div className="deals-page">
      <div className="page-header">
        <div>
          <h1>Deals</h1>
          <p className="tagline">
            Sortiert nach tatsächlich gemessener Preissenkung aus unserer Preishistorie — nicht nach dem
            Streichpreis, den der Shop selbst festlegt.
          </p>
        </div>
      </div>

      <div className="deals-controls">
        <label>
          Zeitraum
          <select value={windowDays} onChange={(e) => update("window_days", e.target.value)}>
            {WINDOW_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Mindestsenkung
          <select value={minDrop} onChange={(e) => update("min_drop_pct", e.target.value)}>
            {MIN_DROP_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Kategorie
          <select value={category} onChange={(e) => update("category", e.target.value)}>
            <option value="">alle</option>
            {categories.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <span className="deals-count">{data.total} Treffer</span>
      </div>

      {loading && <div className="status-message">Lädt…</div>}

      {!loading && data.results.length === 0 && (
        <div className="status-message">
          Keine Preissenkung in diesem Zeitraum. Der Vergleich braucht einen Preis-Snapshot, der mindestens{" "}
          {windowDays} Tage alt ist — bei einem frisch importierten Katalog gibt es den noch nicht.
        </div>
      )}

      {!loading && data.results.length > 0 && (
        <div className="results-grid">
          {data.results.map((item) => (
            <ResultCard key={item.variant_id} item={item}>
              <DealBadge item={item} windowDays={data.window_days} />
            </ResultCard>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => update("page", String(page - 1))}>
            ‹ Zurück
          </button>
          <span>
            Seite {data.page} / {totalPages}
          </span>
          <button disabled={page >= totalPages} onClick={() => update("page", String(page + 1))}>
            Weiter ›
          </button>
        </div>
      )}
    </div>
  );
}
