import { removeSavedSearch, saveSearch, useSavedSearches } from "../collections";
import { describeFilters, hasActiveFilters, searchParamsFromFilters } from "../filters";

/** The complete filter state already lives in the URL, so "save this search"
 *  is just storing that querystring under a name. */
export default function SavedSearches({ filters, onApply }) {
  const searches = useSavedSearches();
  const currentQuery = searchParamsFromFilters(filters, { includePaging: false }).toString();
  const alreadySaved = searches.some((entry) => entry.query === currentQuery);
  const canSave = hasActiveFilters(filters) && !alreadySaved;

  if (!searches.length && !canSave) return null;

  return (
    <div className="saved-searches">
      <span className="saved-searches-label">Gespeicherte Suchen</span>

      {searches.map((entry) => (
        <span key={entry.id} className="chip chip-saved">
          <button type="button" className="chip-apply" onClick={() => onApply(entry.query)} title={entry.query}>
            {entry.name}
          </button>
          <button
            type="button"
            className="chip-x-button"
            aria-label={`„${entry.name}" löschen`}
            onClick={() => removeSavedSearch(entry.id)}
          >
            ×
          </button>
        </span>
      ))}

      {canSave && (
        <button
          type="button"
          className="chip chip-save"
          onClick={() => {
            const suggestion = describeFilters(filters);
            const name = window.prompt("Name für diese Suche:", suggestion);
            if (name && name.trim()) saveSearch(name.trim(), currentQuery);
          }}
        >
          + Aktuelle Suche speichern
        </button>
      )}
      {alreadySaved && <span className="saved-searches-hint">Diese Suche ist gespeichert.</span>}
    </div>
  );
}
