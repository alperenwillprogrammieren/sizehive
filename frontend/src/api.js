const API_BASE = "/api";

export async function fetchSearch(params) {
  const res = await fetch(`${API_BASE}/search?${params.toString()}`);
  if (!res.ok) throw new Error(`search failed: ${res.status}`);
  return res.json();
}

export async function fetchFacets(params) {
  const res = await fetch(`${API_BASE}/facets?${params.toString()}`);
  if (!res.ok) throw new Error(`facets failed: ${res.status}`);
  return res.json();
}

/** Resolves a list of variant ids to current search-result items. Backs the
 *  local collections (Merkliste, zuletzt angesehen), which store ids only. */
export async function fetchVariantsByIds(ids) {
  if (!ids.length) return { results: [] };
  const res = await fetch(`${API_BASE}/variants?ids=${ids.join(",")}`);
  if (!res.ok) throw new Error(`variants batch failed: ${res.status}`);
  return res.json();
}

export async function fetchVariantDetail(variantId) {
  const res = await fetch(`${API_BASE}/variants/${variantId}`);
  if (!res.ok) throw new Error(`variant detail failed: ${res.status}`);
  return res.json();
}

export async function fetchDashboardCoverage() {
  const res = await fetch(`${API_BASE}/dashboard/coverage`);
  if (!res.ok) throw new Error(`dashboard coverage failed: ${res.status}`);
  return res.json();
}
