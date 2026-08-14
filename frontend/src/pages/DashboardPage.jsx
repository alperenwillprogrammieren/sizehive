import { useEffect, useState } from "react";
import { fetchDashboardCoverage } from "../api";

const ATTRIBUTE_LABELS = {
  fit: "Passform",
  rise: "Bundhöhe",
  leg_shape: "Beinform",
  wash: "Waschung",
  material: "Material",
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

export default function DashboardPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboardCoverage().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="status-message">Lädt…</div>;

  return (
    <div className="dashboard-page">
      <h1>Attribut-Abdeckung</h1>
      <p className="tagline">{data.total_products} Produkte insgesamt, über alle Kategorien</p>

      {data.by_category.map((cat) => (
        <div className="category-coverage" key={cat.category}>
          <h2 className="section-title">
            {cat.category} <span className="coverage-note">({cat.total_products} Produkte)</span>
          </h2>
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
