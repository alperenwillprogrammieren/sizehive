import { createContext, useContext } from "react";

// Kept out of watchlist.jsx for the same reason as authContext.js: a file
// that exports a component should export only components.
export const WatchlistContext = createContext(null);

export function useWatchlist() {
  const context = useContext(WatchlistContext);
  if (context === null) throw new Error("useWatchlist must be used inside WatchlistProvider");
  return context;
}
