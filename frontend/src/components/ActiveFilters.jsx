const LABELS = {
  fit: "Passform",
  rise: "Bundhöhe",
  leg_shape: "Beinform",
  wash: "Waschung",
  closure: "Verschluss",
  brand: "Marke",
  color: "Farbe",
  size_w: "W",
  size_l: "L",
  price_min: "ab €",
  price_max: "bis €",
  in_stock_only: "Nur lieferbar",
};

function formatValue(value) {
  return String(value).replace(/_/g, " ");
}

export default function ActiveFilters({ filters, onRemove, onClearAll }) {
  const chips = [];
  for (const key of ["brand", "color"]) {
    for (const value of filters[key] || []) {
      chips.push({ key, value, label: `${LABELS[key]}: ${formatValue(value)}` });
    }
  }
  for (const key of ["fit", "rise", "leg_shape", "wash", "closure"]) {
    if (filters[key]) chips.push({ key, value: filters[key], label: `${LABELS[key]}: ${formatValue(filters[key])}` });
  }
  if (filters.size_w) chips.push({ key: "size_w", value: filters.size_w, label: `${LABELS.size_w}${filters.size_w}` });
  if (filters.size_l) chips.push({ key: "size_l", value: filters.size_l, label: `${LABELS.size_l}${filters.size_l}` });
  if (filters.price_min)
    chips.push({ key: "price_min", value: filters.price_min, label: `${LABELS.price_min}${filters.price_min}` });
  if (filters.price_max)
    chips.push({ key: "price_max", value: filters.price_max, label: `${LABELS.price_max}${filters.price_max}` });
  if (filters.in_stock_only) chips.push({ key: "in_stock_only", value: true, label: LABELS.in_stock_only });

  if (chips.length === 0) return null;

  return (
    <div className="active-filters">
      {chips.map((chip) => (
        <button key={`${chip.key}-${chip.value}`} className="chip" onClick={() => onRemove(chip.key, chip.value)}>
          {chip.label} <span className="chip-x">×</span>
        </button>
      ))}
      <button className="chip chip-clear" onClick={onClearAll}>
        Alle entfernen
      </button>
    </div>
  );
}
