import { useCallback, useSyncExternalStore } from "react";
import { readStore, subscribeStore, writeStore } from "./localStore";

// Client-side collections. Each entry stores only a variant id (plus, for the
// watchlist, the price at the moment of saving) — never a copy of the
// product. The live data is re-fetched from /api/variants?ids=… on every
// view, so a saved entry can't drift out of sync with the catalog.

const WATCHLIST_KEY = "sizehive.watchlist.v1";
const SAVED_SEARCHES_KEY = "sizehive.saved-searches.v1";
const RECENT_KEY = "sizehive.recently-viewed.v1";

const RECENT_LIMIT = 12;

function useKey(key, fallback) {
  const subscribe = useCallback((callback) => subscribeStore(key, callback), [key]);
  return useSyncExternalStore(subscribe, () => readStore(key, fallback), () => fallback);
}

/* ---------------------------------------------------------------- Merkliste */

export function useWatchlist() {
  return useKey(WATCHLIST_KEY, []);
}

export function isWatched(watchlist, variantId) {
  return watchlist.some((entry) => entry.variant_id === variantId);
}

/** Adds or removes; `priceEur` is remembered so the Merkliste can show the
 *  price move since the item was saved. */
export function toggleWatch(variantId, priceEur) {
  const current = readStore(WATCHLIST_KEY, []);
  if (current.some((entry) => entry.variant_id === variantId)) {
    writeStore(WATCHLIST_KEY, current.filter((entry) => entry.variant_id !== variantId));
    return false;
  }
  const entry = {
    variant_id: variantId,
    price_eur_at_save: typeof priceEur === "number" ? priceEur : null,
    saved_at: new Date().toISOString(),
  };
  writeStore(WATCHLIST_KEY, [entry, ...current]);
  return true;
}

export function removeFromWatchlist(variantId) {
  const current = readStore(WATCHLIST_KEY, []);
  writeStore(WATCHLIST_KEY, current.filter((entry) => entry.variant_id !== variantId));
}

export function clearWatchlist() {
  writeStore(WATCHLIST_KEY, []);
}

/* -------------------------------------------------------- Gespeicherte Suchen */

export function useSavedSearches() {
  return useKey(SAVED_SEARCHES_KEY, []);
}

/** `query` is the filter querystring (no paging) — the URL already carries
 *  the complete filter state, so saving a search is just saving that string. */
export function saveSearch(name, query) {
  const current = readStore(SAVED_SEARCHES_KEY, []);
  const withoutDuplicate = current.filter((entry) => entry.query !== query);
  const entry = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, name, query, saved_at: new Date().toISOString() };
  writeStore(SAVED_SEARCHES_KEY, [entry, ...withoutDuplicate]);
  return entry;
}

export function removeSavedSearch(id) {
  const current = readStore(SAVED_SEARCHES_KEY, []);
  writeStore(SAVED_SEARCHES_KEY, current.filter((entry) => entry.id !== id));
}

/* --------------------------------------------------------- Zuletzt angesehen */

export function useRecentlyViewed() {
  return useKey(RECENT_KEY, []);
}

export function recordView(variantId) {
  const current = readStore(RECENT_KEY, []);
  const next = [variantId, ...current.filter((id) => id !== variantId)].slice(0, RECENT_LIMIT);
  // Skip the write (and the re-render it triggers) when nothing moved.
  if (next.length === current.length && next.every((id, i) => id === current[i])) return;
  writeStore(RECENT_KEY, next);
}

export function clearRecentlyViewed() {
  writeStore(RECENT_KEY, []);
}
