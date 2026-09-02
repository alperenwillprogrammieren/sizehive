import { Link, useLocation } from "react-router-dom";
import { clearCompare, useCompareList } from "../collections";

/** Persistent bottom bar shown across all pages while items are queued for
 *  comparison — mirrors how the Merkliste nav badge stays visible everywhere,
 *  but this needs its own affordance since comparing is a cross-page action
 *  (you add items while browsing, then jump to /vergleich once ready). */
export default function CompareBar() {
  const compareList = useCompareList();
  const location = useLocation();

  if (compareList.length === 0 || location.pathname === "/vergleich") return null;

  return (
    <div className="compare-bar">
      <span>{compareList.length} zum Vergleich ausgewählt</span>
      <div className="compare-bar-actions">
        <Link to="/vergleich" className="compare-bar-link">
          Vergleichen
        </Link>
        <button type="button" className="text-button" onClick={clearCompare}>
          Leeren
        </button>
      </div>
    </div>
  );
}
