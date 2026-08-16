import { Link } from "react-router-dom";
import WatchButton from "./WatchButton";

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

/** One product card. `children` renders extra content under the price — used
 *  by the Merkliste to show the price move since the item was saved. */
export function ResultCard({ item, children }) {
  return (
    <article className="result-card">
      <div className="result-image-wrap">
        <Link to={`/product/${item.variant_id}`}>
          <img src={item.image_url} alt={`${item.brand} ${item.model_name}`} loading="lazy" />
        </Link>
        <WatchButton variantId={item.variant_id} priceEur={item.price_eur} className="watch-button-overlay" />
      </div>
      <div className="result-info">
        <Link to={`/product/${item.variant_id}`} className="result-link">
          <div className="result-category">{item.category}</div>
          <div className="result-brand">{item.brand}</div>
          <div className="result-name">{item.model_name}</div>
        </Link>
        <div className="result-meta">
          {item.size_raw} · {formatValue(item.color)} · {item.shop_name}
        </div>
        <div className="result-price">
          <span className="price-current">{item.price_eur.toFixed(2)} €</span>
          {item.discount_pct > 0 && (
            <>
              <span className="price-list">{item.list_price_eur.toFixed(2)} €</span>
              <span className="price-discount">-{item.discount_pct.toFixed(0)}%</span>
            </>
          )}
        </div>
        {children}
        {!item.in_stock && <div className="out-of-stock">Nicht verfügbar</div>}
        <a className="shop-link" href={item.url} target="_blank" rel="noopener noreferrer">
          Zum Shop ↗
        </a>
      </div>
    </article>
  );
}

export default function ResultsList({ results, loading }) {
  if (loading) return <div className="status-message">Lädt…</div>;
  if (results.length === 0) return <div className="status-message">Keine Treffer für diese Filterkombination.</div>;

  return (
    <div className="results-grid">
      {results.map((item) => (
        <ResultCard key={item.variant_id} item={item} />
      ))}
    </div>
  );
}
