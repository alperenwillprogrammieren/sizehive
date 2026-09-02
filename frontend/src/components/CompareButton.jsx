import { COMPARE_LIMIT, toggleCompare, useCompareList } from "../collections";

/** Toggle to add/remove a variant from the comparison tray. Mirrors
 *  WatchButton's interaction (stop propagation so it works inside a card
 *  link), but caps at COMPARE_LIMIT instead of being unlimited. */
export default function CompareButton({ variantId, className = "" }) {
  const compareList = useCompareList();
  const active = compareList.includes(variantId);
  const full = !active && compareList.length >= COMPARE_LIMIT;

  return (
    <button
      type="button"
      className={`compare-button${active ? " active" : ""} ${className}`.trim()}
      aria-pressed={active}
      disabled={full}
      title={full ? `Maximal ${COMPARE_LIMIT} Artikel vergleichbar` : active ? "Vom Vergleich entfernen" : "Zum Vergleich hinzufügen"}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleCompare(variantId);
      }}
    >
      <span aria-hidden="true">⇄</span>
      <span className="sr-only">{active ? "Im Vergleich" : "Vergleichen"}</span>
    </button>
  );
}
