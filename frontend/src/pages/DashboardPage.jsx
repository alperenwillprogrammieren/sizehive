import { useEffect, useState } from "react";
import { fetchAttributePrices, fetchDashboardCoverage, fetchPriceDistribution, fetchShopTrust } from "../api";
import BoxPlotChart from "../components/BoxPlotChart";
import ChartFrame from "../components/ChartFrame";
import DivergingBars from "../components/DivergingBars";

const ATTRIBUTE_LABELS = {
  fit: "Passform",
  rise: "Bundhöhe",
  leg_shape: "Beinform",
  wash: "Waschung",
  fiber: "Material",
  material: "Zusammensetzung",
  stretch: "Stretch",
  closure: "Verschluss",
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

function labelFor(key) {
  return ATTRIBUTE_LABELS[key] || key.replace(/_/g, " ");
}

const GENDER_LABELS = { female: "Damen", male: "Herren", unisex: "Unisex" };
const DIMENSION_LABELS = { category: "Kategorie", brand: "Marke", gender: "Geschlecht" };

/** Aggregate of the per-article discount-honesty check: across everything a
 *  shop currently advertises as reduced, how often was the struck-through
 *  price ever really charged? */
function ShopTrustTable({ shops }) {
  if (!shops || shops.length === 0) return null;

  return (
    <div className="shop-trust">
      <h2 className="section-title">Streichpreis-Ehrlichkeit je Shop</h2>
      <p className="coverage-note">
        Anteil der aktuell beworbenen Rabatte, deren Streichpreis in unserer Historie mindestens einmal
        tatsächlich verlangt wurde.
      </p>
      <table className="trust-table">
        <thead>
          <tr>
            <th>Shop</th>
            <th>Artikel</th>
            <th>mit Rabatt</th>
            <th>Streichpreis nie verlangt</th>
            <th>Vertrauen</th>
            <th>Rabatt laut Shop</th>
            <th>tatsächlich</th>
          </tr>
        </thead>
        <tbody>
          {shops.map((shop) => (
            <tr key={shop.shop_name}>
              <td>{shop.shop_name}</td>
              <td className="num">{shop.variants_total}</td>
              <td className="num">{shop.variants_with_claimed_discount}</td>
              <td className="num">{shop.claimed_discount_never_charged}</td>
              <td className="num">
                {shop.trust_pct === null ? (
                  "—"
                ) : (
                  <span className={`trust-pct ${shop.trust_pct >= 90 ? "good" : shop.trust_pct >= 70 ? "mid" : "bad"}`}>
                    {shop.trust_pct.toFixed(0)} %
                  </span>
                )}
              </td>
              <td className="num">
                {shop.avg_claimed_discount_pct === null ? "—" : `−${shop.avg_claimed_discount_pct.toFixed(0)} %`}
              </td>
              <td className="num">
                {shop.avg_real_discount_pct === null ? "—" : `−${shop.avg_real_discount_pct.toFixed(0)} %`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Price statistics. One filter row scopes both charts below it — never a
 *  filter inside a chart card. */
function PriceStatistics({ categories }) {
  const [dimension, setDimension] = useState("category");
  const [category, setCategory] = useState("");
  const [distribution, setDistribution] = useState(null);
  const [attributes, setAttributes] = useState(null);

  useEffect(() => {
    if (!category && categories.length) setCategory(categories[0]);
  }, [categories, category]);

  useEffect(() => {
    fetchPriceDistribution(dimension)
      .then((data) => {
        if (dimension !== "gender") return setDistribution(data);
        setDistribution({
          ...data,
          groups: data.groups.map((g) => ({ ...g, group: GENDER_LABELS[g.group] || g.group })),
        });
      })
      .catch(console.error);
  }, [dimension]);

  useEffect(() => {
    if (!category) return;
    fetchAttributePrices(category).then(setAttributes).catch(console.error);
  }, [category]);

  return (
    <>
      <h2 className="section-title dashboard-section">Preisstatistik</h2>

      <div className="chart-filters">
        <label>
          Verteilung nach
          <select value={dimension} onChange={(e) => setDimension(e.target.value)}>
            <option value="category">Kategorie</option>
            <option value="brand">Marke</option>
            <option value="gender">Geschlecht</option>
          </select>
        </label>
        <label>
          Attributvergleich für
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {distribution && (
        <ChartFrame
          title={`Preisverteilung je ${DIMENSION_LABELS[dimension] || dimension}`}
          note="Aktuelle Preise. Balken: mittlere 50 % (p25–p75), Strich darin: Median, Antennen: günstigstes und teuerstes Angebot. Gruppen unter 5 Angeboten bleiben außen vor."
          tableHead={[DIMENSION_LABELS[dimension] || dimension, "Angebote", "Min", "p25", "Median", "p75", "Max"]}
          tableRows={distribution.groups.map((group) => [
            group.group,
            String(group.count),
            `${group.min_eur.toFixed(2)} €`,
            `${group.p25_eur.toFixed(2)} €`,
            `${group.median_eur.toFixed(2)} €`,
            `${group.p75_eur.toFixed(2)} €`,
            `${group.max_eur.toFixed(2)} €`,
          ])}
        >
          <BoxPlotChart groups={distribution.groups} />
        </ChartFrame>
      )}

      {attributes && attributes.attributes.length === 0 && (
        <p className="coverage-note">Für {category} gibt es keinen Attributwert mit genug Angeboten zum Vergleich.</p>
      )}

      {attributes?.attributes.map((attribute) => (
        <ChartFrame
          key={attribute.attribute}
          title={`${labelFor(attribute.attribute)}: Preisabweichung`}
          note={`Medianpreis je Wert gegenüber dem Median dieses Attributs (${attribute.median_eur.toFixed(2)} €).`}
          tableHead={["Wert", "Angebote", "Median", "Abweichung"]}
          tableRows={attribute.values.map((value) => [
            value.value.replace(/_/g, " "),
            String(value.count),
            `${value.median_eur.toFixed(2)} €`,
            `${value.delta_pct > 0 ? "+" : ""}${value.delta_pct.toFixed(1)} %`,
          ])}
        >
          <DivergingBars
            rows={attribute.values}
            baselineLabel={`dem Median von ${labelFor(attribute.attribute)}`}
          />
        </ChartFrame>
      ))}
    </>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [trust, setTrust] = useState(null);

  useEffect(() => {
    fetchDashboardCoverage().then(setData).catch(console.error);
    fetchShopTrust().then((result) => setTrust(result.shops)).catch(console.error);
  }, []);

  if (!data) return <div className="status-message">Lädt…</div>;

  return (
    <div className="dashboard-page">
      <h1>Dashboard</h1>

      <ShopTrustTable shops={trust} />

      <PriceStatistics categories={data.by_category.map((cat) => cat.category)} />

      <h2 className="section-title dashboard-section">Attribut-Abdeckung</h2>
      <p className="coverage-note">{data.total_products} Produkte insgesamt, über alle Kategorien</p>

      {data.by_category.map((cat) => (
        <div className="category-coverage" key={cat.category}>
          <h3 className="section-title">
            {cat.category} <span className="coverage-note">({cat.total_products} Produkte)</span>
          </h3>
          <div className="coverage-list">
            {Object.entries(cat.coverage).map(([attr, pct]) => (
              <div className="coverage-row" key={attr}>
                <span className="coverage-label">{labelFor(attr)}</span>
                <div className="coverage-bar-track">
                  <div className="coverage-bar-fill" style={{ width: `${(pct * 100).toFixed(1)}%` }} />
                </div>
                <span className="coverage-pct">{(pct * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
