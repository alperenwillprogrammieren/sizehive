const MULTI_FACET_KEYS = ["category", "brand", "color"];

const LABELS = {
  category: "Kategorie",
  brand: "Marke",
  color: "Farbe",
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
  return LABELS[key] || key.replace(/_/g, " ");
}

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

export default function FacetSidebar({ facets, filters, onUpdateField, onToggleMulti, onUpdateAttr }) {
  const facetKeys = Object.keys(facets);
  const multiKeys = facetKeys.filter((k) => MULTI_FACET_KEYS.includes(k));
  const singleKeys = facetKeys.filter((k) => !MULTI_FACET_KEYS.includes(k));

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
            onChange={(e) => onUpdateField("price_min", e.target.value)}
          />
          <input
            type="number"
            min="0"
            placeholder="bis"
            value={filters.price_max}
            onChange={(e) => onUpdateField("price_max", e.target.value)}
          />
        </div>
      </div>

      <div className="facet-group">
        <h3>Größe (Jeans W/L)</h3>
        <div className="range-inputs">
          <input
            type="number"
            placeholder="W"
            value={filters.size_w}
            onChange={(e) => onUpdateField("size_w", e.target.value)}
          />
          <input
            type="number"
            placeholder="L"
            value={filters.size_l}
            onChange={(e) => onUpdateField("size_l", e.target.value)}
          />
        </div>
      </div>

      <div className="facet-group">
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={filters.in_stock_only}
            onChange={(e) => onUpdateField("in_stock_only", e.target.checked)}
          />
          Nur lieferbar
        </label>
      </div>

      {multiKeys.map((key) => {
        const options = facets[key] || [];
        if (options.length === 0) return null;
        return (
          <div className="facet-group" key={key}>
            <h3>{labelFor(key)}</h3>
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

      {singleKeys.map((key) => {
        const options = facets[key] || [];
        if (options.length === 0) return null;
        return (
          <div className="facet-group" key={key}>
            <h3>{labelFor(key)}</h3>
            <ul className="facet-list">
              {options.map((opt) => {
                const active = filters.attrs[key] === opt.value;
                return (
                  <li key={opt.value}>
                    <button
                      type="button"
                      className={`facet-option${active ? " active" : ""}`}
                      onClick={() => onUpdateAttr(key, active ? "" : opt.value)}
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
