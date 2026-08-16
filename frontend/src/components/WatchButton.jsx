import { useWatchlist } from "../watchlistContext";

/** Heart toggle. `priceEur` is stored alongside the id so the Merkliste can
 *  later show how the price moved since the item was saved. Works the same
 *  logged in (account) and logged out (localStorage). */
export default function WatchButton({ variantId, priceEur, className = "" }) {
  const { isWatched, toggle } = useWatchlist();
  const watched = isWatched(variantId);

  return (
    <button
      type="button"
      className={`watch-button${watched ? " watched" : ""} ${className}`.trim()}
      aria-pressed={watched}
      title={watched ? "Von der Merkliste entfernen" : "Auf die Merkliste"}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        toggle(variantId, priceEur);
      }}
    >
      <span aria-hidden="true">{watched ? "♥" : "♡"}</span>
      <span className="sr-only">{watched ? "Gemerkt" : "Merken"}</span>
    </button>
  );
}
