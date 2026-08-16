import { useEffect, useState } from "react";
import { fetchVariantsByIds } from "./api";

/** Resolves locally stored variant ids (Merkliste, zuletzt angesehen) to
 *  live catalog items. Keyed on the joined ids so a re-render with an equal
 *  but freshly built array doesn't refetch. */
export function useVariantsByIds(ids) {
  const key = ids.join(",");
  const [state, setState] = useState({ items: [], loading: ids.length > 0 });

  useEffect(() => {
    const list = key ? key.split(",").map(Number) : [];
    if (!list.length) {
      setState({ items: [], loading: false });
      return undefined;
    }

    let cancelled = false;
    setState((prev) => ({ ...prev, loading: true }));
    fetchVariantsByIds(list)
      .then((data) => {
        if (!cancelled) setState({ items: data.results, loading: false });
      })
      .catch((err) => {
        console.error(err);
        if (!cancelled) setState({ items: [], loading: false });
      });

    return () => {
      cancelled = true;
    };
  }, [key]);

  return state;
}
