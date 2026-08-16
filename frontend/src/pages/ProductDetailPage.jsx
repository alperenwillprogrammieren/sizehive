import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchVariantDetail } from "../api";
import { recordView } from "../collections";
import PriceAlertBox from "../components/PriceAlertBox";
import PriceChart from "../components/PriceChart";
import PriceVerdict from "../components/PriceVerdict";
import ProductImage from "../components/ProductImage";
import SimilarProducts from "../components/SimilarProducts";
import WatchButton from "../components/WatchButton";

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

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

function AttributeBadge({ name, value, sourceInfo }) {
  const label = ATTRIBUTE_LABELS[name] || name;
  const displayValue = Array.isArray(value)
    ? value.map(formatValue).join(", ")
    : typeof value === "object"
      ? Object.entries(value)
          .map(([k, v]) => `${k.replace(/_pct$/, "")}: ${v}%`)
          .join(", ")
      : typeof value === "boolean"
        ? value
          ? "ja"
          : "nein"
        : formatValue(value);
  const isDerived = sourceInfo && sourceInfo.source !== "feed";

  return (
    <div className="attr-badge">
      <span className="attr-label">{label}</span>
      <span className="attr-value">{displayValue}</span>
      {isDerived && (
        <span className="attr-source" title={`Konfidenz ${(sourceInfo.confidence * 100).toFixed(0)}%`}>
          abgeleitet · {(sourceInfo.confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}

export default function ProductDetailPage() {
  const { variantId } = useParams();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setDetail(null);
    setError(null);
    fetchVariantDetail(variantId)
      .then((data) => {
        setDetail(data);
        recordView(data.variant_id);
      })
      .catch((err) => setError(err.message));
  }, [variantId]);

  if (error) return <div className="status-message">Artikel nicht gefunden.</div>;
  if (!detail) return <div className="status-message">Lädt…</div>;

  return (
    <div className="detail-page">
      <Link to="/" className="back-link">
        ‹ Zurück zur Suche
      </Link>

      <div className="detail-layout">
        <ProductImage
          className="detail-image"
          src={detail.image_url}
          alt={`${detail.brand} ${detail.model_name}`}
          loading="eager"
        />

        <div className="detail-info">
          <div className="result-category">{detail.category}</div>
          <div className="detail-brand">{detail.brand}</div>
          <h1 className="detail-name">{detail.model_name}</h1>
          <div className="detail-meta">
            {detail.size_raw} · {formatValue(detail.color)} · {detail.shop_name}
          </div>

          <div className="detail-price">
            <span className="price-current">{detail.current_price_eur.toFixed(2)} €</span>
            {detail.current_list_price_eur > detail.current_price_eur && (
              <span className="price-list">{detail.current_list_price_eur.toFixed(2)} €</span>
            )}
            <WatchButton variantId={detail.variant_id} priceEur={detail.current_price_eur} />
          </div>
          {!detail.in_stock && <div className="out-of-stock">Nicht verfügbar</div>}

          {detail.percentile_score !== null && (
            <div className="percentile-score">
              Günstiger als <strong>{detail.percentile_score.toFixed(0)}%</strong> der Artikel in {detail.category}
              <span className="percentile-note"> ({detail.comparable_count} verglichen)</span>
            </div>
          )}

          <div className={`discount-check ${detail.list_price_ever_charged ? "honest" : "warn"}`}>
            {detail.list_price_ever_charged
              ? "Der Streichpreis wurde in der Vergangenheit tatsächlich verlangt."
              : "Der Streichpreis wurde in der aufgezeichneten Historie nie tatsächlich verlangt."}
          </div>

          <a className="shop-link" href={detail.url} target="_blank" rel="noopener noreferrer">
            Zum Shop ↗
          </a>

          <PriceAlertBox variantId={detail.variant_id} currentPrice={detail.current_price_eur} />

          <h2 className="section-title">Attribute</h2>
          <div className="attr-grid">
            {Object.entries(detail.attributes).map(([name, value]) => (
              <AttributeBadge key={name} name={name} value={value} sourceInfo={detail.attribute_sources[name]} />
            ))}
          </div>

          {detail.description && (
            <>
              <h2 className="section-title">Beschreibung</h2>
              <p className="detail-description">{detail.description}</p>
            </>
          )}
        </div>
      </div>

      <h2 className="section-title">Preis-Einordnung</h2>
      <PriceVerdict stats={detail.price_stats} currentPrice={detail.current_price_eur} />

      <h2 className="section-title">Preisverlauf</h2>
      <PriceChart points={detail.price_history} />

      <SimilarProducts variantId={detail.variant_id} />
    </div>
  );
}
