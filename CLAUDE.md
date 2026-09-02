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
python -m app.importers.fetch                        # download the real Awin feed (needs AWIN_FEED_URL)
python -m app.importers.run                          # import real feeds from backend/data/live/
python -m app.importers.run --with-samples           # ...plus the generated fixtures in data/samples/
python scripts/purge_sample_shops.py                 # drop sample-fixture shops from a real-data DB
python -m app.extract.run                             # run attribute extraction, print coverage
python scripts/simulate_price_history.py              # optional: backfill demo price history
python -m app.notify.run                              # send price alerts + search-agent digests
python scripts/daily_update.py                        # fetch → import → extract → notify, in one go
uvicorn app.main:app --reload --port 8000              # http://localhost:8000/docs
python -m pytest tests/    # unit tests (normalizers, extractors, price stats, alert rules, tokens)
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

Four catalog tables (`backend/app/models/`), plus the account tables in `models/account.py`
(`app_user`, `login_token`, `user_session`, `watchlist_item`, `price_alert`, `search_agent` —
see "Accounts" below):

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

### Search: typo tolerance, autocomplete, similar articles

- **Typo tolerance is a fallback, not a mode.** The strict `ILIKE '%…%'` runs first; only when
  it returns zero does the query re-run against pg_trgm's `word_similarity` at
  `FUZZY_THRESHOLD`. That keeps the common case exact, and makes the generous threshold
  correct — the alternative to a fuzzy hit is an empty page. `resolve_fuzzy()` is called by
  **both** `/search` and `/facets`, so the sidebar can't describe a different result set than
  the one on screen. The response's `fuzzy` flag is what the UI uses to say so out loud.
- `/api/suggest` has no such fallback — it ORs substring and similarity in one pass, because a
  suggestion list that silently stays empty on a typo is the exact case autocomplete exists for.
- `/api/variants/{id}/similar` ranks by **attribute overlap first, price proximity second**
  (`app/recommend.py`, pure + unit-tested). Same category only — attribute vocabularies don't
  overlap across categories, so an identical price must not imply similarity. Candidates are
  pre-selected in SQL by price proximity and capped before Python scores them.
- The trigram indexes live in the `7c1e4f3a9b02` migration. `CREATE EXTENSION pg_trgm` needs
  privileges the app user may not have in a managed database — that's a deploy prerequisite,
  not something the app does at runtime.

### Dashboard charts

`frontend/src/components/{BoxPlotChart,DivergingBars,ChartFrame}.jsx`, hand-rolled inline SVG
(no chart library, consistent with `PriceChart`). Two rules drive the encoding and shouldn't be
"improved" without reason:

- **Nominal groups get one hue.** Brands and categories have no natural order, so every box wears
  `--viz-series-1`. Colouring them by value would re-encode what the box position already shows.
  One series ⇒ no legend; the title names what's plotted.
- **Deviation from a baseline gets the diverging pair** (`--viz-pos` / `--viz-neg` with
  `--viz-mid` as the neutral zero) — not the status palette: "costs more" isn't "bad".

The viz tokens in `index.css` are validated per mode against `--surface` (lightness band, chroma
floor, CVD separation, normal-vision floor, 3:1 contrast); the dark values are their own selected
steps, not a flip. Every chart ships a **table twin** via `ChartFrame` — tooltips enhance, they
never gate a value — and the filter row sits above the charts it scopes, never inside a card.

### Accounts, alerts and search agents

Accounts exist because price alerts and search agents can't work without server-side identity —
something has to evaluate them while the browser is closed. Everything else stays usable logged
out.

- **Passwordless.** `app/auth/tokens.py` (pure, unit-tested) defines token generation, hashing and
  expiry; `app/auth/service.py` issues the magic link, burns it on use, and mints a session.
  Neither login tokens nor session tokens are stored in the clear — only SHA-256 hashes. Unsalted
  is correct here (32 bytes of `secrets`, nothing to brute-force) and keeps lookup an indexed
  equality; do not copy this for passwords. Sessions ride an httpOnly cookie, so every account
  call in `frontend/src/api.js` goes through `authed()` with `credentials: "include"`.
- **`app/notify/run.py`** is the CLI that does the actual work, meant to run after an import:
  `python -m app.importers.run && python -m app.notify.run`. Idempotent by design.
- **`app/notify/rules.py`** holds the fire/don't-fire decision as pure functions. Two anti-spam
  rules matter more than the trigger: a repeat notification needs a *strictly lower* price than
  the one last reported (`last_notified_price_cents`), and an alert without a target price only
  fires on a record low. Change these and you change how much mail users get — the tests in
  `tests/test_notify_rules.py` pin every branch.
- **A search agent is a stored filter querystring** — the same string the frontend puts in the
  URL. `filters_from_query_string()` in `app/api/search.py` parses it without an HTTP request, and
  tolerates junk (a stale or hand-edited query drops the bad filter instead of failing the run).
  "New" means `variant.created_at > last_run_at`, so a re-import of an existing offer never
  counts. `last_run_at` starts at creation time — an agent never mails the existing catalog.
- **Without `smtp_host` configured, mail is logged instead of sent** (`app/notify/mailer.py`), so
  login and notifications are fully exercisable in dev. `app/main.py` therefore configures logging
  at INFO — at the default WARNING those lines vanish and dev login becomes impossible.

### Client-side state (works logged out)

Everything user-specific also exists without an account, in `localStorage` behind
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

The Merkliste has **two interchangeable backends**: `watchlist.jsx` serves the localStorage list
when logged out and the account's list when logged in. Components (`WatchButton`,
`WatchlistPage`) only ever call `useWatchlist()` and don't know which is active. Logging in
doesn't move anything automatically — the Merkliste page offers a one-way import, and entries
already on the server keep their original `price_cents_at_save`, since overwriting a historical
measurement would falsify the delta.

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

### Extractor vocabularies are tuned against the *real* corpus

The original extractors were written and validated against
`scripts/generate_sample_feeds.py` output — which was generated to contain
exactly the phrases the rules look for. That closed loop reported ~37 % coverage for
`wash`/`rise`/`leg_shape`/`closure`/`material` on jeans and ~22 % for `sole_type`/`closure_type` on
sneakers; against real shop copy all of those were **0 %**. When touching an extractor, measure on
real data (`python -m app.extract.run` prints per-category coverage), never on the fixtures.

Two rules that fall out of German shop copy specifically:

- **Word-start anchoring, not substring** (`phrase_in` in `app/extract/common.py`). German compounds
  prepend, so a plain `"wolle" in text` tags every *Baumwolle* product as wool. The phrase start is
  anchored to a word boundary; the *end* deliberately is not, because inflection appends
  (`"recycelt"` must keep matching *recycelter*).
- **`fiber` vs `material`.** `extract_material` parses compositions ("98 % Baumwolle, 2 % Elasthan")
  and feeds the `cotton_min` filter. Real copy usually names a fibre with no percentage at all
  ("T-Shirt aus Ecovero"), so `fiber` captures that as a separate, facetable scalar.
- **`sustainability` holds verifiable claims only** — GOTS, bio-zertifiziert, fair, vegan, recycelt.
  Bare marketing adjectives ("nachhaltig") are deliberately excluded: mixing an unverifiable
  self-description in with GOTS makes the filter meaningless, which is the same principle as not
  ranking by a shop-controlled `list_price`.

`tests/test_extract_real_corpus.py` pins all of this to strings copied from live products.

Feed text is HTML-escaped at source ("full forest &amp;amp; orange"); `clean_text` in
`app/importers/common.py` unescapes it during import.

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
`app.importers.run --with-samples` → `app.extract.run` → `scripts/simulate_price_history.py`. That
stops being appropriate once real affiliate feeds are wired up — at that point schema changes need a
real migration with backfill, not a reset.

**That point has been reached**: the database now holds the real Unipolar feed, so
`app.importers.run` imports live feeds only and the fixtures are opt-in behind `--with-samples`.
Sample rows carry picsum.photos placeholder images and invented brands, which are
indistinguishable from real products in the UI once mixed in. `scripts/purge_sample_shops.py`
removes them again if they do get imported.

`scripts/daily_update.py` chains fetch → import → extract → notify and is registered as the Windows
scheduled task "sizehive daily update" (daily 05:00, per-user, `scripts/daily_update.bat` wrapper).
It exists because price history only accrues through repeated imports — a catalogue imported once
makes every article look like it has always cost today's price, which blinds the whole
measured-vs-claimed-discount feature. A failed fetch aborts before the import rather than
re-importing yesterday's file, which would append a duplicate-price snapshot into that history.
Note **extraction must follow every import**: new products land with empty `attributes` until
`app.extract.run` has seen them, and stale extraction silently empties the facet sidebar.

Variant `image_url` and `url` are **refreshed on every import** (see `find_or_create_variant`) —
unlike price, they carry no history worth keeping, and a moved image or rotated affiliate deeplink
just means the stored value is wrong. Identity fields (`shop_sku`, `ean`, size, color) are never
touched. The real Awin feed's `merchant_image_url` (the shop's original, ~1600px) is preferred over
`aw_image_url`, whose CDN caps height at 200px.

## Explicitly out of scope

Cross-shop reviews, size conversion between systems
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
