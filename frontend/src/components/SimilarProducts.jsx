import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSimilar } from "../api";
import ProductImage from "./ProductImage";

const ATTRIBUTE_LABELS = {
  fit: "Passform",
  rise: "Bundhöhe",
  leg_shape: "Beinform",
  wash: "Waschung",
  closure: "Verschluss",
  stretch: "Stretch",
  sleeve: "Ärmel",
  neckline: "Ausschnitt",
  print: "Print",
  upper_material: "Obermaterial",
  sole_type: "Sohle",
  closure_type: "Verschlussart",
  style: "Schafthöhe",
};

function labelFor(key) {
  return ATTRIBUTE_LABELS[key] || key.replace(/_/g, " ");
}

/** Articles described like this one. The shared attributes are shown, because
 *  "why is this similar?" is the interesting part of a catalog built on
 *  garment attributes. */
export default function SimilarProducts({ variantId }) {
  const [items, setItems] = useState([]);

  useEffect(() => {
    let cancelled = false;
    fetchSimilar(variantId)
      .then((data) => {
        if (!cancelled) setItems(data.results);
      })
      .catch((err) => console.error(err));
    return () => {
      cancelled = true;
    };
  }, [variantId]);

  if (items.length === 0) return null;

  return (
    <section className="similar-section">
      <h2 className="section-title">Ähnlich beschriebene Artikel</h2>
      <p className="coverage-note">
        Gewichtet nach übereinstimmenden Attributen, danach nach Preisnähe — innerhalb derselben Kategorie.
      </p>
      <ul className="similar-list">
        {items.map((item) => (
          <li key={item.variant_id}>
            <Link to={`/product/${item.variant_id}`} className="similar-item">
              <ProductImage src={item.image_url} alt={`${item.brand} ${item.model_name}`} />
              <span className="similar-brand">{item.brand}</span>
              <span className="similar-name">{item.model_name}</span>
              <span className="similar-price">{item.price_eur.toFixed(2)} €</span>
              {item.shared_attributes.length > 0 && (
                <span className="similar-shared">
                  gleich: {item.shared_attributes.map(labelFor).join(", ")}
                </span>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
