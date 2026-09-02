import { Link } from "react-router-dom";
import { clearCompare, removeFromCompare, useCompareList } from "../collections";
import { useVariantsByIds } from "../useVariants";
import ProductImage from "../components/ProductImage";

const ATTRIBUTE_LABELS = {
  fit: "Passform",
  rise: "Bundhöhe",
  leg_shape: "Beinform",
  wash: "Waschung",
  closure: "Verschluss",
  stretch: "Stretch",
  material: "Material",
  pockets: "Taschen",
  sustainability: "Nachhaltigkeit",
  sleeve: "Ärmel",
  neckline: "Ausschnitt",
  print: "Print",
  upper_material: "Obermaterial",
  sole_type: "Sohle",
  closure_type: "Verschlussart",
  style: "Schafthöhe",
};

function formatValue(value) {
  if (Array.isArray(value)) return value.map(formatValue).join(", ");
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([k, v]) => `${k.replace(/_pct$/, "")}: ${v}%`)
      .join(", ");
  }
  if (typeof value === "boolean") return value ? "ja" : "nein";
  return String(value).replace(/_/g, " ");
}

/** Side-by-side comparison of up to COMPARE_LIMIT items. Reuses the same
 *  id-only-in-localStorage + batch-refetch pattern as the Merkliste, so a
 *  comparison never shows a price that's gone stale since it was queued. */
export default function ComparePage() {
  const compareList = useCompareList();
  const { items, loading } = useVariantsByIds(compareList);

  // Preserve the order items were added in, not whatever order the batch
  // endpoint happens to return.
  const ordered = compareList.map((id) => items.find((item) => item.variant_id === id)).filter(Boolean);

  const attributeKeys = [...new Set(ordered.flatMap((item) => Object.keys(item.attributes || {})))];

  if (compareList.length === 0) {
    return (
      <div className="status-message">
        Noch keine Artikel zum Vergleich ausgewählt. Klicke bei Suchergebnissen auf ⇄, um sie hinzuzufügen.
      </div>
    );
  }
  if (loading) return <div className="status-message">Lädt…</div>;

  const rows = [
    { label: "Kategorie", render: (item) => item.category },
    { label: "Preis", render: (item) => `${item.price_eur.toFixed(2)} €` },
    {
      label: "Rabatt",
      render: (item) => (item.discount_pct > 0 ? `−${item.discount_pct.toFixed(0)}%` : "—"),
    },
    { label: "Größe", render: (item) => item.size_raw },
    { label: "Farbe", render: (item) => formatValue(item.color) },
    { label: "Shop", render: (item) => item.shop_name },
    { label: "Verfügbarkeit", render: (item) => (item.in_stock ? "Lieferbar" : "Nicht verfügbar") },
    ...attributeKeys.map((key) => ({
      label: ATTRIBUTE_LABELS[key] || key.replace(/_/g, " "),
      render: (item) => (item.attributes[key] !== undefined ? formatValue(item.attributes[key]) : "—"),
    })),
  ];

  return (
    <div className="compare-page">
      <div className="page-header">
        <h1>Vergleich</h1>
        <button type="button" className="text-button" onClick={clearCompare}>
          Alle entfernen
        </button>
      </div>

      <div className="compare-table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th />
              {ordered.map((item) => (
                <th key={item.variant_id}>
                  <button
                    type="button"
                    className="compare-remove"
                    onClick={() => removeFromCompare(item.variant_id)}
                    title="Aus dem Vergleich entfernen"
                  >
                    ×
                  </button>
                  <Link to={`/product/${item.variant_id}`}>
                    <ProductImage
                      src={item.image_url}
                      alt={`${item.brand} ${item.model_name}`}
                      className="compare-image"
                    />
                  </Link>
                  <Link to={`/product/${item.variant_id}`} className="compare-title">
                    <div className="result-brand">{item.brand}</div>
                    <div className="result-name">{item.model_name}</div>
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {ordered.map((item) => (
                  <td key={item.variant_id}>{row.render(item)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
