const API_BASE = "/api";

/** Account endpoints authenticate via an httpOnly session cookie, so every
 *  one of them must send credentials. */
async function authed(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const error = new Error(`${method} ${path} failed: ${res.status}`);
    error.status = res.status;
    try {
      error.detail = (await res.json()).detail;
    } catch {
      error.detail = null;
    }
    throw error;
  }
  return res.status === 204 ? null : res.json();
}

export const auth = {
  requestLink: (email) => authed("/auth/request-link", { method: "POST", body: { email } }),
  verify: (token) => authed("/auth/verify", { method: "POST", body: { token } }),
  me: () => authed("/auth/me"),
  logout: () => authed("/auth/logout", { method: "POST" }),
};

export const account = {
  watchlist: () => authed("/account/watchlist"),
  addWatch: (variant_id, price_eur_at_save) =>
    authed("/account/watchlist", { method: "POST", body: { variant_id, price_eur_at_save } }),
  removeWatch: (variantId) => authed(`/account/watchlist/${variantId}`, { method: "DELETE" }),
  importWatchlist: (items) => authed("/account/watchlist/import", { method: "POST", body: { items } }),

  alerts: () => authed("/account/alerts"),
  createAlert: (variant_id, target_price_eur) =>
    authed("/account/alerts", { method: "POST", body: { variant_id, target_price_eur } }),
  deleteAlert: (variantId) => authed(`/account/alerts/${variantId}`, { method: "DELETE" }),

  agents: () => authed("/account/agents"),
  createAgent: (name, query) => authed("/account/agents", { method: "POST", body: { name, query } }),
  deleteAgent: (id) => authed(`/account/agents/${id}`, { method: "DELETE" }),
};

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

export async function fetchDeals(params) {
  const res = await fetch(`${API_BASE}/deals?${params.toString()}`);
  if (!res.ok) throw new Error(`deals failed: ${res.status}`);
  return res.json();
}

export async function fetchShopTrust() {
  const res = await fetch(`${API_BASE}/dashboard/shop-trust`);
  if (!res.ok) throw new Error(`shop trust failed: ${res.status}`);
  return res.json();
}

export async function fetchDashboardCoverage() {
  const res = await fetch(`${API_BASE}/dashboard/coverage`);
  if (!res.ok) throw new Error(`dashboard coverage failed: ${res.status}`);
  return res.json();
}
