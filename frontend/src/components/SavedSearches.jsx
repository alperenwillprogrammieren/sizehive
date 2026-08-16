import { useState } from "react";
import { account } from "../api";
import { useAuth } from "../authContext";
import { removeSavedSearch, saveSearch, useSavedSearches } from "../collections";
import { describeFilters, hasActiveFilters, searchParamsFromFilters } from "../filters";

/** The complete filter state already lives in the URL, so "save this search"
 *  is just storing that querystring under a name — and a search agent is the
 *  same string handed to the server so it keeps watching while you're away. */
export default function SavedSearches({ filters, onApply }) {
  const searches = useSavedSearches();
  const { user } = useAuth();
  const [agentState, setAgentState] = useState(null);
  const currentQuery = searchParamsFromFilters(filters, { includePaging: false }).toString();
  const alreadySaved = searches.some((entry) => entry.query === currentQuery);
  const canSave = hasActiveFilters(filters) && !alreadySaved;

  const makeAgent = async (name, query) => {
    try {
      await account.createAgent(name, query);
      setAgentState({ ok: true, message: `Suchagent „${name}" ist aktiv.` });
    } catch (err) {
      setAgentState({
        ok: false,
        message:
          err.detail === "agent for this search already exists"
            ? "Für diese Suche gibt es schon einen Agenten."
            : "Der Suchagent konnte nicht angelegt werden.",
      });
    }
  };

  if (!searches.length && !canSave) return null;

  return (
    <div className="saved-searches">
      <span className="saved-searches-label">Gespeicherte Suchen</span>

      {searches.map((entry) => (
        <span key={entry.id} className="chip chip-saved">
          <button type="button" className="chip-apply" onClick={() => onApply(entry.query)} title={entry.query}>
            {entry.name}
          </button>
          {user && (
            <button
              type="button"
              className="chip-agent"
              title="Als Suchagent aktivieren — meldet neue Treffer per E-Mail"
              onClick={() => makeAgent(entry.name, entry.query)}
            >
              🔔
            </button>
          )}
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
      {agentState && (
        <span className={agentState.ok ? "saved-searches-hint" : "auth-error inline"}>{agentState.message}</span>
      )}
    </div>
  );
}
