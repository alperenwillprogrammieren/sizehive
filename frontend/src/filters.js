export const MULTI_KEYS = ["brand", "color"];
export const SINGLE_KEYS = ["fit", "rise", "leg_shape", "wash", "closure"];
export const RANGE_KEYS = ["size_w", "size_l", "price_min", "price_max"];

export const DEFAULT_FILTERS = {
  brand: [],
  color: [],
  fit: "",
  rise: "",
  leg_shape: "",
  wash: "",
  closure: "",
  size_w: "",
  size_l: "",
  price_min: "",
  price_max: "",
  in_stock_only: false,
  sort: "newest",
  page: 1,
};

export function filtersFromSearchParams(sp) {
  const f = { ...DEFAULT_FILTERS };
  for (const key of MULTI_KEYS) {
    const values = sp.getAll(key);
    if (values.length) f[key] = values;
  }
  for (const key of [...SINGLE_KEYS, ...RANGE_KEYS]) {
    if (sp.has(key)) f[key] = sp.get(key);
  }
  if (sp.has("in_stock_only")) f.in_stock_only = sp.get("in_stock_only") === "true";
  if (sp.has("sort")) f.sort = sp.get("sort");
  if (sp.has("page")) f.page = parseInt(sp.get("page"), 10) || 1;
  return f;
}

export function searchParamsFromFilters(f, { includePaging = true } = {}) {
  const sp = new URLSearchParams();
  for (const key of MULTI_KEYS) {
    for (const value of f[key] || []) sp.append(key, value);
  }
  for (const key of SINGLE_KEYS) {
    if (f[key]) sp.set(key, f[key]);
  }
  for (const key of RANGE_KEYS) {
    if (f[key] !== "" && f[key] !== null && f[key] !== undefined) sp.set(key, f[key]);
  }
  if (f.in_stock_only) sp.set("in_stock_only", "true");
  if (includePaging) {
    sp.set("sort", f.sort || "newest");
    sp.set("page", String(f.page || 1));
    sp.set("page_size", "20");
  }
  return sp;
}
