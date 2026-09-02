import { Link } from "react-router-dom";
import ProductImage from "./ProductImage";
import WatchButton from "./WatchButton";
import CompareButton from "./CompareButton";

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
          <ProductImage src={item.image_url} alt={`${item.brand} ${item.model_name}`} />
        </Link>
        {item.discount_pct > 0 && <span className="discount-badge">−{item.discount_pct.toFixed(0)} %</span>}
        <div className="card-overlay-actions">
          <WatchButton variantId={item.variant_id} priceEur={item.price_eur} className="watch-button-overlay" />
          <CompareButton variantId={item.variant_id} className="compare-button-overlay" />
        </div>
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
          <span className={`price-current${item.discount_pct > 0 ? " reduced" : ""}`}>
            {item.price_eur.toFixed(2)} €
          </span>
          {item.discount_pct > 0 && <span className="price-list">{item.list_price_eur.toFixed(2)} €</span>}
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

/** While a new filter/page is loading, the previous grid stays visible
 *  (dimmed) instead of being replaced by a spinner — avoids the layout
 *  jumping to zero height and back on every filter click. Only a genuinely
 *  empty first load or a zero-result page fall back to a status message. */
export default function ResultsList({ results, loading }) {
  if (loading && results.length === 0) return <div className="status-message">Lädt…</div>;
  if (!loading && results.length === 0) {
    return <div className="status-message">Keine Treffer für diese Filterkombination.</div>;
  }

  return (
    <div className={`results-grid${loading ? " results-grid-loading" : ""}`}>
      {results.map((item) => (
        <ResultCard key={item.variant_id} item={item} />
      ))}
    </div>
  );
}
