import { Link } from "react-router-dom";

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

export default function ResultsList({ results, loading }) {
  if (loading) return <div className="status-message">Lädt…</div>;
  if (results.length === 0) return <div className="status-message">Keine Treffer für diese Filterkombination.</div>;

  return (
    <div className="results-grid">
      {results.map((item) => (
        <article className="result-card" key={item.variant_id}>
          <Link to={`/product/${item.variant_id}`}>
            <img src={item.image_url} alt={`${item.brand} ${item.model_name}`} loading="lazy" />
          </Link>
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
            {!item.in_stock && <div className="out-of-stock">Nicht verfügbar</div>}
            <a className="shop-link" href={item.url} target="_blank" rel="noopener noreferrer">
              Zum Shop ↗
            </a>
          </div>
        </article>
      ))}
    </div>
  );
}
