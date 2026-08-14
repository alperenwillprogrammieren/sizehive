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
};

export default function DashboardPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboardCoverage().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="status-message">Lädt…</div>;

  return (
    <div className="dashboard-page">
      <h1>Attribut-Abdeckung</h1>
      <p className="tagline">
        {data.total_products} Produkte insgesamt · {data.products_with_fit_and_wash} (
        {data.products_with_fit_and_wash_pct.toFixed(1)}%) haben sowohl Passform als auch Waschung
      </p>

      <div className="coverage-list">
        {Object.entries(data.coverage).map(([attr, pct]) => (
          <div className="coverage-row" key={attr}>
            <span className="coverage-label">{ATTRIBUTE_LABELS[attr] || attr}</span>
            <div className="coverage-bar-track">
              <div className="coverage-bar-fill" style={{ width: `${(pct * 100).toFixed(1)}%` }} />
            </div>
            <span className="coverage-pct">{(pct * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
