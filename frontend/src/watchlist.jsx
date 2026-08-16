import { useCallback, useEffect, useMemo, useState } from "react";
import { account } from "./api";
import { useAuth } from "./authContext";
import {
  clearWatchlist as clearLocal,
  readLocalWatchlist,
  removeFromWatchlist as removeLocal,
  toggleWatch as toggleLocal,
  useLocalWatchlist,
} from "./collections";

import { WatchlistContext } from "./watchlistContext";

/** One Merkliste API for the whole app, backed by localStorage when logged
 *  out and by the account when logged in. Components (WatchButton,
 *  WatchlistPage) never need to know which of the two is active. */
export function WatchlistProvider({ children }) {
  const { user } = useAuth();
  const localEntries = useLocalWatchlist();
  const [serverEntries, setServerEntries] = useState([]);
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await account.watchlist();
      setServerEntries(data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) reload();
    else setServerEntries([]);
  }, [user, reload]);

  const entries = user ? serverEntries : localEntries;

  const isWatched = useCallback(
    (variantId) => entries.some((entry) => entry.variant_id === variantId),
    [entries]
  );

  const toggle = useCallback(
    async (variantId, priceEur) => {
      if (!user) {
        toggleLocal(variantId, priceEur);
        return;
      }
      if (isWatched(variantId)) await account.removeWatch(variantId);
      else await account.addWatch(variantId, typeof priceEur === "number" ? priceEur : null);
      await reload();
    },
    [user, isWatched, reload]
  );

  const remove = useCallback(
    async (variantId) => {
      if (!user) {
        removeLocal(variantId);
        return;
      }
      await account.removeWatch(variantId);
      await reload();
    },
    [user, reload]
  );

  const clear = useCallback(async () => {
    if (!user) {
      clearLocal();
      return;
    }
    await Promise.all(serverEntries.map((entry) => account.removeWatch(entry.variant_id)));
    await reload();
  }, [user, serverEntries, reload]);

  /** One-way merge of the browser list into the account. The local list is
   *  kept afterwards — it is what an eventual logout falls back to. */
  const importLocal = useCallback(async () => {
    const local = readLocalWatchlist();
    if (!local.length) return { imported: 0, skipped: 0 };
    const result = await account.importWatchlist(
      local.map((entry) => ({ variant_id: entry.variant_id, price_eur_at_save: entry.price_eur_at_save }))
    );
    await reload();
    return result;
  }, [reload]);

  const value = useMemo(
    () => ({
      entries,
      loading,
      isWatched,
      toggle,
      remove,
      clear,
      importLocal,
      backend: user ? "server" : "local",
      localCount: localEntries.length,
    }),
    [entries, loading, isWatched, toggle, remove, clear, importLocal, user, localEntries.length]
  );

  return <WatchlistContext.Provider value={value}>{children}</WatchlistContext.Provider>;
}
