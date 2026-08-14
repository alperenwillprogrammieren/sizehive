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

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }, []);

  const toggleMultiFilter = useCallback((key, value) => {
    setFilters((prev) => {
      const current = prev[key] || [];
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
      return { ...prev, [key]: next, page: 1 };
    });
  }, []);

  const removeFilterValue = useCallback((key, value) => {
    setFilters((prev) => {
      if (Array.isArray(prev[key])) return { ...prev, [key]: prev[key].filter((v) => v !== value), page: 1 };
      return { ...prev, [key]: DEFAULT_FILTERS[key], page: 1 };
    });
  }, []);

  const clearAll = useCallback(() => setFilters({ ...DEFAULT_FILTERS }), []);

  const setPage = useCallback((page) => setFilters((prev) => ({ ...prev, page })), []);

  const totalPages = Math.max(1, Math.ceil(searchData.total / (searchData.page_size || 20)));

  return (
    <>
      <ActiveFilters filters={filters} onRemove={removeFilterValue} onClearAll={clearAll} />

      <div className="app-body">
        <FacetSidebar
          facets={facetsData.facets}
          filters={filters}
          onUpdate={updateFilter}
          onToggleMulti={toggleMultiFilter}
        />

        <main className="results-area">
          <div className="results-toolbar">
            <span>{searchData.total} Treffer</span>
            <select value={filters.sort} onChange={(e) => updateFilter("sort", e.target.value)}>
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
