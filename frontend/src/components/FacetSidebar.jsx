import { useMemo, useState } from "react";

const MULTI_FACET_KEYS = ["category", "gender", "brand", "color"];
const DEFAULT_OPEN_KEYS = ["category", "gender", "brand", "color"];
const SEARCHABLE_MIN_OPTIONS = 8;
// Real catalogues have hundreds of distinct colour names ("chalk white /
// jet black"), which turned the sidebar into a 7000px column dwarfing the
// results next to it. Long lists are cut to their highest-count values —
// the ones a facet list is for — with the rest a click away.
const MAX_VISIBLE_OPTIONS = 8;

const LABELS = {
  category: "Kategorie",
  gender: "Geschlecht",
  brand: "Marke",
  color: "Farbe",
  fit: "Passform",
  rise: "Bundhöhe",
  leg_shape: "Beinform",
  wash: "Waschung",
  closure: "Verschluss",
  stretch: "Stretch",
  fiber: "Material",
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

const GENDER_LABELS = { female: "Damen", male: "Herren", unisex: "Unisex" };

function formatValue(key, value) {
  if (key === "gender") return GENDER_LABELS[value] || value;
  return String(value).replace(/_/g, " ");
}

/** A collapsible filter section. Uses native <details> so open/closed state
 *  survives re-renders (facets refresh on every search) without extra state.
 *
 *  Two modes: plain `children` for the fixed price/size inputs, or
 *  `options` + `renderOption` for facet value lists — the latter gets its
 *  own search box once the list is long enough that scanning it by eye
 *  stops being faster than typing (SEARCHABLE_MIN_OPTIONS). */
function FacetGroup({ title, defaultOpen = false, children, options, renderOption }) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(false);
  const searchable = options && options.length >= SEARCHABLE_MIN_OPTIONS;
  const filteredOptions = useMemo(() => {
    if (!options) return null;
    if (!query.trim()) return options;
    const q = query.trim().toLowerCase();
    return options.filter((opt) => String(opt.value).replace(/_/g, " ").toLowerCase().includes(q));
  }, [options, query]);

  // An active search has already narrowed the list, so don't truncate on
  // top of it — that would hide the very match being looked for.
  const truncating = filteredOptions && !expanded && !query.trim()
    && filteredOptions.length > MAX_VISIBLE_OPTIONS;
  const visibleOptions = truncating ? filteredOptions.slice(0, MAX_VISIBLE_OPTIONS) : filteredOptions;

  return (
    <details className="facet-group" open={defaultOpen}>
      <summary>{title}</summary>
      <div className="facet-group-body">
        {searchable && (
          <input
            type="text"
            className="facet-search"
            placeholder={`${title} durchsuchen…`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onClick={(e) => e.stopPropagation()}
          />
        )}
        {options ? (
          visibleOptions.length > 0 ? (
            <>
              <ul className="facet-list">{visibleOptions.map(renderOption)}</ul>
              {(truncating || expanded) && filteredOptions.length > MAX_VISIBLE_OPTIONS && (
                <button type="button" className="facet-more" onClick={() => setExpanded((v) => !v)}>
                  {expanded
                    ? "weniger anzeigen"
                    : `alle ${filteredOptions.length} anzeigen`}
                </button>
              )}
            </>
          ) : (
            <div className="facet-empty">Keine Treffer für „{query}“</div>
          )
        ) : (
          children
        )}
      </div>
    </details>
  );
}

export default function FacetSidebar({ facets, filters, onUpdateField, onToggleMulti, onUpdateAttr }) {
  const facetKeys = Object.keys(facets);
  const multiKeys = facetKeys.filter((k) => MULTI_FACET_KEYS.includes(k));
  const singleKeys = facetKeys.filter((k) => !MULTI_FACET_KEYS.includes(k));

  return (
    <aside className="facet-sidebar">
      <FacetGroup title="Preis (€)" defaultOpen>
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
      </FacetGroup>

      <FacetGroup title="Größe (Jeans W/L)" defaultOpen>
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
      </FacetGroup>

      <div className="facet-group facet-group-plain">
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
          <FacetGroup
            title={labelFor(key)}
            defaultOpen={DEFAULT_OPEN_KEYS.includes(key)}
            key={key}
            options={options}
            renderOption={(opt) => (
              <li key={opt.value}>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={(filters[key] || []).includes(opt.value)}
                    onChange={() => onToggleMulti(key, opt.value)}
                  />
                  <span>{formatValue(key, opt.value)}</span>
                  <span className="count">{opt.count}</span>
                </label>
              </li>
            )}
          />
        );
      })}

      {singleKeys.map((key) => {
        const options = facets[key] || [];
        if (options.length === 0) return null;
        return (
          <FacetGroup
            title={labelFor(key)}
            defaultOpen={DEFAULT_OPEN_KEYS.includes(key)}
            key={key}
            options={options}
            renderOption={(opt) => {
              const active = filters.attrs[key] === opt.value;
              return (
                <li key={opt.value}>
                  <button
                    type="button"
                    className={`facet-option${active ? " active" : ""}`}
                    onClick={() => onUpdateAttr(key, active ? "" : opt.value)}
                  >
                    <span>{formatValue(key, opt.value)}</span>
                    <span className="count">{opt.count}</span>
                  </button>
                </li>
              );
            }}
          />
        );
      })}
    </aside>
  );
}
