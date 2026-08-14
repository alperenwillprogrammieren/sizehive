import { useCallback, useEffect, useState } from "react";
import { fetchFacets, fetchSearch } from "../api";
import { DEFAULT_FILTERS, filtersFromSearchParams, searchParamsFromFilters } from "../filters";
import FacetSidebar from "../components/FacetSidebar";
import ActiveFilters from "../components/ActiveFilters";
import ResultsList from "../components/ResultsList";

export default function SearchPage() {
  const [filters, setFilters] = useState(() =>
    filtersFromSearchParams(new URLSearchParams(window.location.search))
  );
  const [searchData, setSearchData] = useState({ total: 0, results: [], page: 1, page_size: 20 });
  const [facetsData, setFacetsData] = useState({ facets: {} });
  const [loading, setLoading] = useState(false);
  const [qInput, setQInput] = useState(filters.q);

  useEffect(() => {
    const searchParams = searchParamsFromFilters(filters, { includePaging: true });
    window.history.replaceState(null, "", `?${searchParams.toString()}`);

    const facetsParams = searchParamsFromFilters(filters, { includePaging: false });

    let cancelled = false;
    setLoading(true);
    Promise.all([fetchSearch(searchParams), fetchFacets(facetsParams)])
      .then(([search, facets]) => {
        if (cancelled) return;
        setSearchData(search);
        setFacetsData(facets);
      })
      .catch((err) => console.error(err))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [filters]);

  // Free-text input is debounced locally so every keystroke doesn't fire a request.
  useEffect(() => setQInput(filters.q), [filters.q]);
  useEffect(() => {
    const handle = setTimeout(() => {
      setFilters((prev) => (prev.q === qInput ? prev : { ...prev, q: qInput, page: 1 }));
    }, 350);
    return () => clearTimeout(handle);
  }, [qInput]);

  const updateField = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }, []);

  const toggleMultiFilter = useCallback((key, value) => {
    setFilters((prev) => {
      const current = prev[key] || [];
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
      return { ...prev, [key]: next, page: 1 };
    });
  }, []);

  const updateAttr = useCallback((key, value) => {
    setFilters((prev) => {
      const attrs = { ...prev.attrs };
      if (value) attrs[key] = value;
      else delete attrs[key];
      return { ...prev, attrs, page: 1 };
    });
  }, []);

  const removeMulti = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: (prev[key] || []).filter((v) => v !== value), page: 1 }));
  }, []);

  const clearField = useCallback((key) => {
    setFilters((prev) => ({ ...prev, [key]: DEFAULT_FILTERS[key], page: 1 }));
  }, []);

  const clearAttr = useCallback((key) => {
    setFilters((prev) => {
      const attrs = { ...prev.attrs };
      delete attrs[key];
      return { ...prev, attrs, page: 1 };
    });
  }, []);

  const clearAll = useCallback(() => setFilters({ ...DEFAULT_FILTERS, attrs: {} }), []);

  const setPage = useCallback((page) => setFilters((prev) => ({ ...prev, page })), []);

  const totalPages = Math.max(1, Math.ceil(searchData.total / (searchData.page_size || 20)));

  return (
    <>
      <div className="search-bar">
        <input
          type="search"
          placeholder="Suche nach Marke, Modell, Beschreibung…"
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
        />
      </div>

      <ActiveFilters
        filters={filters}
        onRemoveMulti={removeMulti}
        onClearField={clearField}
        onClearAttr={clearAttr}
        onClearAll={clearAll}
      />

      <div className="app-body">
        <FacetSidebar
          facets={facetsData.facets}
          filters={filters}
          onUpdateField={updateField}
          onToggleMulti={toggleMultiFilter}
          onUpdateAttr={updateAttr}
        />

        <main className="results-area">
          <div className="results-toolbar">
            <span>{searchData.total} Treffer</span>
            <select value={filters.sort} onChange={(e) => updateField("sort", e.target.value)}>
              <option value="newest">Neuheit</option>
              <option value="price_asc">Preis aufsteigend</option>
              <option value="price_desc">Preis absteigend</option>
              <option value="discount_desc">Rabatthöhe</option>
            </select>
          </div>

          <ResultsList results={searchData.results} loading={loading} />

          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={filters.page <= 1} onClick={() => setPage(filters.page - 1)}>
                ‹ Zurück
              </button>
              <span>
                Seite {searchData.page} / {totalPages}
              </span>
              <button disabled={filters.page >= totalPages} onClick={() => setPage(filters.page + 1)}>
                Weiter ›
              </button>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
