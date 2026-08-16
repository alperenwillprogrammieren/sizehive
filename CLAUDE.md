# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What sizehive is

A webapp that makes clothing searchable across shops. Individual shops each have their own
filters that don't work across sites, and price comparators (Idealo etc.) compare price but not
clothing attributes. Sizehive's differentiator: faceted search across *many* garment attributes
simultaneously (fit, rise, leg shape, wash, material, stretch, closure, etc.), not just size and
price, across all connected shops in one query — plus free-text search combinable with those
filters.

`docs/SPEC.md` is the original product brief (German) that drove the initial build (milestones
M0–M7, MVP scoped to one category: men's jeans). `docs/DECISIONS.md` records what was actually
built and why, including a post-MVP extension that added two more categories (T-Shirts, Sneaker)
and free-text search — read it before making architectural changes, it explains the non-obvious
tradeoffs. Both are historical/design records; this file describes current state.

## Commands

```bash
docker compose up -d db                             # Postgres (host port 55432, see DECISIONS.md)
```

Backend (from `backend/`, with `.venv` activated):
```bash
alembic upgrade head                                 # apply migrations
python -m app.importers.run                          # load backend/data/samples/*.{csv,xml}
python -m app.extract.run                             # run attribute extraction, print coverage
python scripts/simulate_price_history.py              # optional: backfill demo price history
uvicorn app.main:app --reload --port 8000              # http://localhost:8000/docs
python -m pytest tests/                                # unit tests (normalizers, extractors)
python scripts/generate_sample_feeds.py                # regenerate backend/data/samples/*
```

After any model/migration change during local dev, the fastest path is
`alembic downgrade base && alembic upgrade head` followed by re-running the three data-pipeline
commands above — see "Dev data lifecycle" below for why that's fine here specifically.

Frontend (from `frontend/`):
```bash
npm install
npm run dev                                            # http://localhost:5173, proxies /api -> :8000
```

## Architecture

**Repo layout:** `backend/` (FastAPI + SQLAlchemy + Alembic) and `frontend/` (React + Vite) as
separate top-level folders. Docker Compose runs Postgres only; both dev servers run natively.

### Data model

Four tables (`backend/app/models/`):

- `shop` — id, name, slug, affiliate_network
- `product` — id, brand, model_name, category, gender, description, `attributes` (JSONB, GIN
  index), `attribute_sources` (JSONB)
- `variant` — id, product_id, shop_id, shop_sku, ean (nullable), size_raw, size_w, size_l, color,
  url, image_url, created_at
- `price_snapshot` — id, variant_id, price_cents, list_price_cents, in_stock, captured_at

`price_snapshot` rows are **append-only, never overwritten** — price history is a side effect of
repeated imports. `product.category` is a plain string column (no enum, no category table): adding
a category is data, not a migration. `product.description`, `variant.image_url`, and
`variant.created_at` aren't in the original spec's proposed model — see `docs/DECISIONS.md` for
why each was added.

### Category = configuration, not schema

This is the load-bearing design decision, proven out by three categories today
(`Herrenjeans`, `T-Shirts`, `Sneaker`) with more addable without touching the pipeline:

- `app/taxonomy.py` — category → gender mapping.
- `app/extract/registry.py` — category → `AttributeExtractor` instance
  (`app/extract/{rules,tshirts,sneakers}.py`, all implementing the `AttributeExtractor` Protocol
  in `app/extract/base.py`: keyword/regex extraction from title+description into
  `{attribute: ExtractedAttribute(value, source, confidence)}`). `app/extract/run.py` picks the
  extractor per product via `get_extractor(product.category)`.
- `app/extract/report.py` — coverage report is computed **per category**, discovering attribute
  keys dynamically per category's own products rather than assuming a fixed list (different
  categories have disjoint attribute vocabularies — a T-Shirt has no `wash`).
- `app/api/search.py` — Kür-attribute filtering is generic: any query param that isn't in
  `RESERVED_PARAMS` is applied as `Product.attributes[<param name>].astext == value` (see
  `SearchFilters.attrs`). `/api/facets` discovers which attribute keys to facet on via
  `SELECT DISTINCT jsonb_object_keys(attributes)`, minus `NON_SCALAR_ATTRS` (nested/array values
  like `material`/`sustainability`, which have their own dedicated comparison — `cotton_min`,
  `sustainability` containment).
- Frontend mirrors this: `frontend/src/filters.js` treats any non-reserved URL param as a generic
  attribute filter (`filters.attrs`); `FacetSidebar.jsx` renders whatever facet keys the API
  returns, with a label dictionary that falls back to the raw key name for anything not curated.

**Adding a category**: add an entry to `app/taxonomy.py` + `app/extract/registry.py`, write an
extractor class, generate/import some data with that `category` value. No DB migration, no new
API parameters, no required frontend change (labels are a nice-to-have, not a dependency).

### Client-side state (no accounts)

There is no user table and no auth. Everything user-specific lives in `localStorage` behind
`frontend/src/localStore.js`, a small reactive wrapper (one subscriber set per key, exposed via
`useSyncExternalStore`, parsed values cached so `getSnapshot` stays referentially stable):

- `frontend/src/collections.js` — Merkliste, gespeicherte Suchen, zuletzt angesehen.
- `frontend/src/theme.js` — `system`/`light`/`dark`. "system" is resolved in JS and stamped as
  `data-theme` on `<html>` before first paint (`initTheme()` in `main.jsx`), so the CSS only ever
  needs `:root` and `:root[data-theme="dark"]` — no `prefers-color-scheme` in the stylesheet — and
  a dark reload never flashes light. All colors go through the tokens in `index.css`.

**These collections store variant ids only** — never a copy of the product. The live data is
re-fetched from `GET /api/variants?ids=1,2,3` (`useVariants.js`) on every view, so a saved entry
can't show a stale price or a since-deleted article. The one exception is the Merkliste's
`price_eur_at_save`, which is deliberately a historical snapshot: it's what the "günstiger/teurer
als beim Merken" delta compares against. A gespeicherte Suche stores nothing but the filter
querystring, because the URL already *is* the complete filter state.

### Measured vs. claimed discount

`price_snapshot` being append-only is what makes this possible, and it's the differentiator a
price comparator without its own history can't copy: a shop's `list_price` is a number the shop
controls, so nothing user-facing ranks by it.

- `app/pricing/history.py` — pure functions (no ORM, no DB, unit-tested in
  `tests/test_pricing_history.py`) defining what all-time low, "not cheaper since N days", and
  **real discount** (current price vs. the highest price we ever observed being charged) mean.
  Consumed by `/api/variants/{id}`'s `price_stats`.
- `app/api/deals.py` — `GET /api/deals` ranks by the drop against the newest snapshot at least
  `window_days` old. That reference point, not a max or average, is what lets the UI name a date
  ("−49 % gegenüber 138,97 € vom 04.08."). Variants without a snapshot that old drop out rather
  than being compared against a guessed baseline, so a long `window_days` on a freshly imported
  catalog correctly returns nothing.
- `GET /api/dashboard/shop-trust` rolls the per-article honesty check up per shop.
- `price_cents` are integers — discount expressions multiply by `100.0` first, or SQL integer
  division floors every drop to zero.

### Attribute provenance

Every attribute in `product.attributes` has a matching entry in `product.attribute_sources`:
`{"source": "feed"|"rule"|"llm", "confidence": float}`. `fit`/`price`/`size`/etc. from the feed
itself don't go through `attributes` at all — they're real columns/Pflicht data. Only Kür
(derived) attributes go through the extractor pipeline and carry provenance; the frontend marks
these "abgeleitet · NN%" wherever they're shown (search results' `attributes` field, and the
detail page's attribute badges).

### Import pipeline

`app/importers/adapters.py` has one parser per feed format (`parse_awin_csv`, `parse_belboon_csv`,
`parse_tradedoubler_xml`) normalizing to a common row shape, including reading `category` directly
from the feed (not a hardcoded constant — feeds are multi-category). `app/importers/importer.py`
matches products by normalized `(brand, model_name, category, gender)` — brand is canonicalized
via `app/normalize/brand.py` *before* matching, which is what lets the same product sold by two
shops under different brand spellings merge into one product row. Variants match on
`(shop_id, shop_sku)`, the anchor for idempotent re-imports (new variant rows never duplicate;
every row always appends a fresh `price_snapshot`).

`app/normalize/{size,brand,color}.py` are static, hand-maintained alias tables / regex parsers —
not fuzzy matching. Unparseable values (e.g. a bare EU shoe size or letter size hitting the
jeans-only W/L size parser) are logged via `logging`, not silently dropped or guessed; that's
correct, expected behavior for non-jeans sizes, not a bug.

### Dev data lifecycle

`backend/data/samples/*.{csv,xml}` are generated, not hand-written — `scripts/generate_sample_feeds.py`
produces deliberately messy multi-category data (mixed size notations, ~20% missing EANs,
inconsistent brand spellings, attributes only in free text). Because this is local sample data with
no real users, the established pattern after any schema or normalization change during development
has been: `alembic downgrade base && alembic upgrade head`, then re-run
`app.importers.run` → `app.extract.run` → `scripts/simulate_price_history.py`. That stops being
appropriate once real affiliate feeds are wired up — at that point schema changes need a real
migration with backfill, not a reset.

## Explicitly out of scope

Cross-shop reviews, user accounts and anything that needs server-side identity (the Merkliste and
gespeicherte Suchen are per-browser `localStorage` only — see "Client-side state" above; price
alerts and notifications would need real accounts and are not built), size conversion between systems
(W32 ↔ 48 ↔ EU36, or between the W/L, S–XXL, and EU-shoe-size systems now all present in the
catalog). Categories beyond the current three are addable per the pattern above but each still
needs a hand-written extractor — there's no zero-effort "any category" support, despite filtering
being fully generic once attributes exist.

## Milestones (historical)

M0–M7 (see `docs/SPEC.md` for full detail, `docs/DECISIONS.md` for what was actually decided)
took the project from an empty repo to: base setup, data model, sample-feed import (idempotent),
size/brand/color normalization, rule-based attribute extraction, faceted search API, a React
search frontend, and per-article statistics (percentile price score, price-history chart,
discount-honesty check, coverage dashboard). All complete. A subsequent request added free-text
search and the multi-category architecture described above.
