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
