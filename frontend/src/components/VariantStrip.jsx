import { Link } from "react-router-dom";
import { useVariantsByIds } from "../useVariants";
import ProductImage from "./ProductImage";

/** Compact horizontal row of variants — used for "zuletzt angesehen", where
 *  full result cards would dominate the page. */
export default function VariantStrip({ ids, title, onClear }) {
  const { items, loading } = useVariantsByIds(ids);
  if (loading || items.length === 0) return null;

  return (
    <section className="variant-strip-section">
      <div className="variant-strip-header">
        <h2 className="section-title">{title}</h2>
        {onClear && (
          <button type="button" className="text-button" onClick={onClear}>
            Verlauf leeren
          </button>
        )}
      </div>
      <ul className="variant-strip">
        {items.map((item) => (
          <li key={item.variant_id}>
            <Link to={`/product/${item.variant_id}`} className="variant-strip-item">
              <ProductImage src={item.image_url} alt={`${item.brand} ${item.model_name}`} />
              <span className="variant-strip-brand">{item.brand}</span>
              <span className="variant-strip-price">{item.price_eur.toFixed(2)} €</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
