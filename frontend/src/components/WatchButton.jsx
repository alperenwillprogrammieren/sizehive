import { isWatched, toggleWatch, useWatchlist } from "../collections";

/** Heart toggle. `priceEur` is stored alongside the id so the Merkliste can
 *  later show how the price moved since the item was saved. */
export default function WatchButton({ variantId, priceEur, className = "" }) {
  const watchlist = useWatchlist();
  const watched = isWatched(watchlist, variantId);

  return (
    <button
      type="button"
      className={`watch-button${watched ? " watched" : ""} ${className}`.trim()}
      aria-pressed={watched}
      title={watched ? "Von der Merkliste entfernen" : "Auf die Merkliste"}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleWatch(variantId, priceEur);
      }}
    >
      <span aria-hidden="true">{watched ? "♥" : "♡"}</span>
      <span className="sr-only">{watched ? "Gemerkt" : "Merken"}</span>
    </button>
  );
}
