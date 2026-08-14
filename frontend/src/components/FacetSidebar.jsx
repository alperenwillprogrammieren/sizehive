const SINGLE_FACETS = [
  { key: "fit", label: "Passform" },
  { key: "rise", label: "Bundhöhe" },
  { key: "leg_shape", label: "Beinform" },
  { key: "wash", label: "Waschung" },
  { key: "closure", label: "Verschluss" },
];

const MULTI_FACETS = [
  { key: "brand", label: "Marke" },
  { key: "color", label: "Farbe" },
];

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

export default function FacetSidebar({ facets, filters, onUpdate, onToggleMulti }) {
  return (
    <aside className="facet-sidebar">
      <div className="facet-group">
        <h3>Preis (€)</h3>
        <div className="range-inputs">
          <input
            type="number"
            min="0"
            placeholder="von"
            value={filters.price_min}
            onChange={(e) => onUpdate("price_min", e.target.value)}
          />
          <input
            type="number"
            min="0"
            placeholder="bis"
            value={filters.price_max}
            onChange={(e) => onUpdate("price_max", e.target.value)}
          />
        </div>
      </div>

      <div className="facet-group">
        <h3>Größe</h3>
        <div className="range-inputs">
          <input
            type="number"
            placeholder="W"
            value={filters.size_w}
            onChange={(e) => onUpdate("size_w", e.target.value)}
          />
          <input
            type="number"
            placeholder="L"
            value={filters.size_l}
            onChange={(e) => onUpdate("size_l", e.target.value)}
          />
        </div>
      </div>

      <div className="facet-group">
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={filters.in_stock_only}
            onChange={(e) => onUpdate("in_stock_only", e.target.checked)}
          />
          Nur lieferbar
        </label>
      </div>

      {MULTI_FACETS.map(({ key, label }) => {
        const options = facets[key] || [];
        if (options.length === 0) return null;
        return (
          <div className="facet-group" key={key}>
            <h3>{label}</h3>
            <ul className="facet-list">
              {options.map((opt) => (
                <li key={opt.value}>
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={(filters[key] || []).includes(opt.value)}
                      onChange={() => onToggleMulti(key, opt.value)}
                    />
                    <span>{formatValue(opt.value)}</span>
                    <span className="count">{opt.count}</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        );
      })}

      {SINGLE_FACETS.map(({ key, label }) => {
        const options = facets[key] || [];
        if (options.length === 0) return null;
        return (
          <div className="facet-group" key={key}>
            <h3>{label}</h3>
            <ul className="facet-list">
              {options.map((opt) => {
                const active = filters[key] === opt.value;
                return (
                  <li key={opt.value}>
                    <button
                      type="button"
                      className={`facet-option${active ? " active" : ""}`}
                      onClick={() => onUpdate(key, active ? "" : opt.value)}
                    >
                      <span>{formatValue(opt.value)}</span>
                      <span className="count">{opt.count}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </aside>
  );
}
