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
  size_w: "W",
  size_l: "L",
  price_min: "ab €",
  price_max: "bis €",
  in_stock_only: "Nur lieferbar",
  q: "Suche",
};

function labelFor(key) {
  return LABELS[key] || key.replace(/_/g, " ");
}

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

export default function ActiveFilters({ filters, onRemoveMulti, onClearField, onClearAttr, onClearAll }) {
  const chips = [];
  for (const key of ["category", "brand", "color"]) {
    for (const value of filters[key] || []) {
      chips.push({ label: `${labelFor(key)}: ${formatValue(value)}`, onRemove: () => onRemoveMulti(key, value) });
    }
  }
  for (const [key, value] of Object.entries(filters.attrs || {})) {
    if (value) chips.push({ label: `${labelFor(key)}: ${formatValue(value)}`, onRemove: () => onClearAttr(key) });
  }
  if (filters.q) chips.push({ label: `${labelFor("q")}: ${filters.q}`, onRemove: () => onClearField("q") });
  if (filters.size_w)
    chips.push({ label: `${labelFor("size_w")}${filters.size_w}`, onRemove: () => onClearField("size_w") });
  if (filters.size_l)
    chips.push({ label: `${labelFor("size_l")}${filters.size_l}`, onRemove: () => onClearField("size_l") });
  if (filters.price_min)
    chips.push({ label: `${labelFor("price_min")}${filters.price_min}`, onRemove: () => onClearField("price_min") });
  if (filters.price_max)
    chips.push({ label: `${labelFor("price_max")}${filters.price_max}`, onRemove: () => onClearField("price_max") });
  if (filters.in_stock_only)
    chips.push({ label: labelFor("in_stock_only"), onRemove: () => onClearField("in_stock_only") });

  if (chips.length === 0) return null;

  return (
    <div className="active-filters">
      {chips.map((chip) => (
        <button key={chip.label} className="chip" onClick={chip.onRemove}>
          {chip.label} <span className="chip-x">×</span>
        </button>
      ))}
      <button className="chip chip-clear" onClick={onClearAll}>
        Alle entfernen
      </button>
    </div>
  );
}
