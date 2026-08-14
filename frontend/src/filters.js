// Structural query params with dedicated UI controls. Everything else in
// the URL is treated as a generic Kür-attribute filter (see `attrs` below)
// — this mirrors the backend's generic filtering in app/api/search.py, so
// a new category's attributes (e.g. "sleeve", "upper_material") work here
// without any frontend code change either.
export const MULTI_KEYS = ["brand", "color", "category"];
export const RANGE_KEYS = ["size_w", "size_l", "price_min", "price_max"];
const RESERVED_KEYS = new Set([
  ...MULTI_KEYS,
  ...RANGE_KEYS,
  "in_stock_only",
  "q",
  "sort",
  "page",
  "page_size",
  "cotton_min",
  "sustainability",
]);

export const DEFAULT_FILTERS = {
  brand: [],
  color: [],
  category: [],
  size_w: "",
  size_l: "",
  price_min: "",
  price_max: "",
  in_stock_only: false,
  q: "",
  sort: "newest",
  page: 1,
  attrs: {},
};

export function filtersFromSearchParams(sp) {
  const f = { ...DEFAULT_FILTERS, attrs: {} };
  for (const key of MULTI_KEYS) {
    const values = sp.getAll(key);
    if (values.length) f[key] = values;
  }
  for (const key of RANGE_KEYS) {
    if (sp.has(key)) f[key] = sp.get(key);
  }
  if (sp.has("q")) f.q = sp.get("q");
  if (sp.has("in_stock_only")) f.in_stock_only = sp.get("in_stock_only") === "true";
  if (sp.has("sort")) f.sort = sp.get("sort");
  if (sp.has("page")) f.page = parseInt(sp.get("page"), 10) || 1;
  for (const key of sp.keys()) {
    if (!RESERVED_KEYS.has(key)) f.attrs[key] = sp.get(key);
  }
  return f;
}

export function searchParamsFromFilters(f, { includePaging = true } = {}) {
  const sp = new URLSearchParams();
  for (const key of MULTI_KEYS) {
    for (const value of f[key] || []) sp.append(key, value);
  }
  for (const key of RANGE_KEYS) {
    if (f[key] !== "" && f[key] !== null && f[key] !== undefined) sp.set(key, f[key]);
  }
  if (f.q) sp.set("q", f.q);
  if (f.in_stock_only) sp.set("in_stock_only", "true");
  for (const [key, value] of Object.entries(f.attrs || {})) {
    if (value) sp.set(key, value);
  }
  if (includePaging) {
    sp.set("sort", f.sort || "newest");
    sp.set("page", String(f.page || 1));
    sp.set("page_size", "20");
  }
  return sp;
}
